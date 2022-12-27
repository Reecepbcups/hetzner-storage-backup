import os
import re
import shutil
import time
import zipfile
from datetime import datetime

import pysftp
from pymongo import MongoClient

from config import CONFIG
from cosmetics import cprint
from notifications import discord_notification
from system import getCurrentHostname, getRamUsage, getStorageAmount


def getBackupConfig() -> dict:
    backup_data = CONFIG['backups']
    return backup_data

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
TIME_FORMAT = '%b-%d-%Y_%I-%M-%S%p'

class Backup:
    '''
    Create a class which can zip files & ignore files if they match any given regex expression.
    It should take in the ROOT_PATH to start to compile. THen loop through all sub directories and files
    '''

    def __init__(self, debug=False, showIgnored=True, showSuccess=True):
        self.current_time = datetime.now().strftime(TIME_FORMAT)
        self.showIgnored = showIgnored
        self.showSuccess = showSuccess

        # check if backups is in config
        if not 'backups' in CONFIG:
            cprint("&cNo backup section in config, grab example from 'secret.json.example'")
            exit(0)


        self.root_paths = CONFIG['backups']['parent-paths']        
        self.backup_path = CONFIG['backups']['save-location']
        self.max_local_backups = CONFIG['backups']['max-local-backups']
        if self.max_local_backups <= 0:
            self.max_local_backups = 0            

        # make directory if it doesn't exist
        if not os.path.exists(self.backup_path):
            os.makedirs(self.backup_path)

        self.discord_webhook = CONFIG['discord-webhook']
        self.debug = debug
        self.save_relative = CONFIG['backups']['save-relative']
                
        self.zipfilename = f"{getCurrentHostname()}_{self.current_time}.zip"
        self.backup_file_name = os.path.join(self.backup_path, self.zipfilename)        
        

    def backup_mongodb(self, mongoDBConfig):
        client = MongoClient(mongoDBConfig['backup-uri'])        
        # confirm client is connected
        if client is None:
            cprint("&cMongoDB client is not connected")
            exit(0)

        self.mongodb_abs_location = os.path.join(self.backup_path, f'mongodb_dump_{self.current_time}')
        res = os.system(f"mongodump --uri={mongoDBConfig['backup-uri']} --out {self.mongodb_abs_location}")
        if res != 0:
            cprint("&cMongoDB backup failed!")
            exit(0)

        # print(self.mongodb_abs_location)
        # exit(0)

        # Adds mongodb absolute location to the zip file to be looped through
        self.root_paths[self.mongodb_abs_location] = []
        # exit(0)


    def delete_oldest_files_in_dir_if_over_max(self):
        # Remove oldest backup so we don't store too many
        list_of_backups = os.listdir(self.backup_path)         

        if len(list_of_backups) > self.max_local_backups:
            for i in range(len(list_of_backups) - self.max_local_backups):
                full_paths = [f"{os.path.join(self.backup_path, x)}" for x in os.listdir(self.backup_path)]                
                oldest_file = min(full_paths, key=os.path.getctime)
                os.remove(oldest_file)
                cprint(f"&cRemoved {oldest_file} as it was the oldest backup")

    def zip_files(self):
        # ! IMPORTANT: Switch to https://pypi.org/project/aiozipstream/
        self.zip_file = zipfile.ZipFile(self.backup_file_name, "w", compression=zipfile.ZIP_DEFLATED)

        # use pymongo to save the backup to the database
        # https://stackoverflow.com/questions/24610484/pymongo-mongoengine-equivalent-of-mongodump ??
        mongoConfig = CONFIG['backups']['database']['mongodb']        
        if(mongoConfig['enabled']):
            self.backup_mongodb(mongoConfig)

        for root_path in self.root_paths:            
            if not os.path.isdir(root_path):
                cprint(f"\n&c{root_path} is not a directory, ignoring...")
                continue

            ignore_regex = CONFIG['backups']['parent-paths'][root_path]
            # print(root_path, ignore_regex)

            text_output = ""
            log = ""
            for root, dirs, files in os.walk(root_path):        
                for file in files:
                    abs_path = os.path.join(root, file)
                    relative_filename = str(abs_path).replace(root_path, "")                    
                    
                    # try:
                    #     if not any(re.search(regex, abs_path) for regex in ignore_regex):
                    #         print(abs_path)
                    # except Exception as e:
                    #     pass         

                    if not any(re.search(regex, abs_path) for regex in ignore_regex):
                        if self.save_relative:
                            self.zip_file.write(abs_path, arcname=relative_filename) # saves just from the rooth path onwards
                        else:
                            self.zip_file.write(os.path.join(root, file)) # saves them as teh full abs path      
                        if self.debug and self.showSuccess:
                            # cprint(f"&a{relative_filename}")
                            text_output += f"&a{relative_filename}\n"
                        log += f"+ {abs_path}\n"
                    else:
                        if self.debug and self.showIgnored:
                            if 'node_modules' not in abs_path:
                                text_output += f"&c{relative_filename} ignored\n"

                        if 'node_modules' not in abs_path:
                            log += f"- {abs_path}\n"
                        
                    if self.debug and text_output.count('\n') % 25 == 0:
                        cprint(text_output)
                        text_output = ""
                            
        self.zip_file.close()
        
        # delete folder self.mongodb_abs_location
        if(mongoConfig['enabled']):
            if len(self.mongodb_abs_location) > 3:
                shutil.rmtree(self.mongodb_abs_location)
            else:
                print(f"Safety check hit, can't delete {self.mongodb_abs_location}")        

        # if there is a discord webhook, then send a notification.
        if len(self.discord_webhook) > 0:
            fileSizeMB = round(os.path.getsize(self.backup_file_name) / 1024 / 1024, 4)
            size, used, free, storagePercent = getStorageAmount()
            totalRam, usedRam, percentUsed = getRamUsage()
            values = {
                "Backup (MB)": [str(fileSizeMB), True],
                "Backup (GB)": [str(round(fileSizeMB / 1024, 4)), True],                
                "To Hetzner": [str(CONFIG['backups']['hetzner-sftp']['enabled']), True],
                "MongoDB": [str(mongoConfig['enabled']), True],
                "Directories": ['\n'.join(self.root_paths.keys()), False],
                "Storage": [f"{used}/{size} ({storagePercent} used) - Free: {free}", False],
                "RAM": [f"{usedRam}/{totalRam} ({round(float(percentUsed), 1)}% used)", False],                
            }

            time_passed = (datetime.now() - datetime.strptime(self.current_time, TIME_FORMAT)).seconds

            discord_notification(
                url=self.discord_webhook, 
                title=f"Panel - Backup - {getCurrentHostname()}",
                description=f"Backup of {self.zipfilename} | ({time_passed}s)",
                color="11ff44",
                values=values,
                imageLink="https://media.istockphoto.com/vectors/digital-signage-pixel-icon-tech-element-vector-logo-icon-illustrator-vector-id1164466990?k=20&m=1164466990&s=612x612&w=0&h=K5Zp0dtbjKWQS9CdOO53O09EKphYnxZTqDHppSMZ8Rk=",
                footerText=""
            )                  

    # Requires a Hetzner Storage Box (sftp, $3/Month for 1TB)    
    def send_file_to_sftp_server(self):
        hetzner = CONFIG['backups']['hetzner-sftp']
        REMOTE_BACKUP_DIR = hetzner['remote-dir']
        if not hetzner['enabled']: 
            return
                   
        timer_start_seconds = time.time()
        try:            
            cnopts = pysftp.CnOpts()
            cnopts.hostkeys = None
            print("Uploading backup to Hetzner SFTP server...")
            with pysftp.Connection(
                hetzner['server-url'], 
                username=hetzner['username'], 
                password=hetzner['password'],
                cnopts=cnopts
            ) as sftp:
                # .cd, .listdir("path"), .get, .put, .makedirs, .rmdir
                # check that REMOTE_BACKUP_DIR exists, if not make it
                if not sftp.exists(REMOTE_BACKUP_DIR):
                    sftp.makedirs(REMOTE_BACKUP_DIR)

                abs_path=os.path.join(REMOTE_BACKUP_DIR, os.path.basename(self.backup_file_name))            
                sftp.put(self.backup_file_name, remotepath=abs_path)

            print("Upload to Hetzner finished!")


            discord_notification(
                url=self.discord_webhook, 
                title=f"Panel - Upload - {getCurrentHostname()}",
                description=f"Completed upload -> Hetzner in {round(time.time() - timer_start_seconds, 2)} seconds",
                color="00ff00",                
                imageLink="https://cdn.icon-icons.com/icons2/2407/PNG/512/hetzner_icon_146165.png",
                footerText=""
            )
        except Exception as e:
            print("Error sending backup to Hetzner SFTP server", e)
            discord_notification(
                url=self.discord_webhook, 
                title=f"Panel - Upload failed - {getCurrentHostname()}",
                description=f"Upload failed -> Hetzner. Reason: {e}",
                color="ff0000",                
                imageLink="https://cdn.icon-icons.com/icons2/2407/PNG/512/hetzner_icon_146165.png",
                footerText=""
            )
            return