# Hetzner Storage Backup

This is a simple program to backup, zip, and upload files via sFTP to a Hetzner Storage Box ($4/Mo for 1 TB of space).
It requires just some configuration, the storage box account information, and a Linux machine (bare metal or VPS from any provider).

## Installation

```sh
# install required dependencies
python3 -m pip install -r requirements.txt

# copy the default file to the new config file you edit
cp secret.json.example secret.json

# Edit this file with the proper regex files you want to ignore, and folders you want to include.
# NOTE: if you want to match all, ensure you do '.*' as '*' does not work for standard python regex.
# Ex: '.*test/' will ignore 'hello_test/', even though there is no actual period (.) in it.


# BE SURE TO RUN THIS FROM THE ROOT OF WHAT YOU SET 'save-location' IN THE CONFIG
# EDITOR=nano crontab -e
0 2 * * * /usr/bin/python3 /root/hetzner-storage-backup/src/main.py

# Run every night at 2am:            0 2 * * *
# Sunday at 1AM:                     0 1 * * 0
# First day of the month at 3:20PM: 20 15 1 * *
```
