# May be easier to just put all config locations in here to reduce complexity of config.yml having some & here having 1.
import json
import os
from os.path import dirname as parentDir

FILE = f"{parentDir(parentDir(__file__))}/secret.json"
try:
    with open(FILE) as f:
        CONFIG = json.load(f)             
except Exception as e:
    print(f"\nError loading secret.json: {e}\nMAKE SURE YOU 'cp secret.json.example secret.json'")
    CONFIG = {}
    exit(0)  

def saveConfig():
    with open(FILE, 'w') as f:
        json.dump(CONFIG, f, indent=4)