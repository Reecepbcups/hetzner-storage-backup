'''
Reece Williams | Dec 2022
Hetzner Backup Script for Linux Based Machines with Discord Notification Support
'''

from backup import Backup

__version__ = "0.0.1"



debugging = True  

print(f"Backup Run. Debugging: {debugging=}")
b = Backup(debug=debugging)
b.zip_files()
b.send_file_to_sftp_server()