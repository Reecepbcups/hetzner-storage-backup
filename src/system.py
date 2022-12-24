import os
import shlex
import datetime
import subprocess
import sys

def getStorageAmount():
    storage = os.popen("""df -h / | grep /""").read().strip().split()
    size = storage[1]
    used = storage[2]
    free = storage[3]
    percentUsed = storage[4]
    print(f"{size=} {used=} {free=} {percentUsed=}")
    return size, used, free, percentUsed

def getRamUsage():
    totalRam = os.popen("""free -h | grep Mem | awk '{print $2}'""").read().strip()
    usedRam = os.popen("""free -h | grep Mem | awk '{print $3}'""").read().strip()

    percentUsed = os.popen("""free -m | grep Mem | awk '{print (($3/$2)*100)}'""").read().strip()
    print(f"System is using {percentUsed}% of TOTAL RAM ({usedRam}/{totalRam})")
    return totalRam, usedRam, percentUsed

def getLargestDirs(path: str, num: int = 5):
    # du -h /root/juno/ | sort -rh | head -10
    output = os.popen(f"du -h {path} | sort -rh | head -{num}").read().strip()
    return output


def getCurrentHostname():
    return os.popen("hostname").read().strip()

def getNetworkUsage():
    usage = os.popen("""ip -h -s link""").read()
    print(usage)