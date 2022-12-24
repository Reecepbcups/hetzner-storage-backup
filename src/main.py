'''
Reece Williams | Dec 2022
Hetzner Backup Script for Linux Based Machines with Discord Notification Support
'''

from backup import Backup

__version__ = "0.0.1"

print(f"Backup Run")
b = Backup(debug=True)
b.zip_files()
b.send_file_to_sftp_server()
b.delete_oldest_files_in_dir_if_over_max()