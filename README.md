# Hetzner Storage Backup

This is a simple program to backup, zip, and upload files via sFTP to a Hetzner Storage Box ($4/Mo for 1 TB of space).
It requires just some configuration, the storage box account information, and a Linux machine (bare metal or VPS from any provider).

This code is mainly pulled forward from my other project [Minecraft-Panel](https://github.com/Reecepbcups/minecraft-panel)

```sh
# Every night at 2am
0 2 * * * /usr/bin/python3 /root/hetzner-storage-backup/src/main.py
```
