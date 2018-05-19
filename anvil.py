import os
from os import listdir
from os.path import isfile,join

from core.logger import log
from config import ENABLED_ZONES

EXTENSIONS_PATH = 'extensions/'

def launch():
    
    print("##########################################################")
    print('''
            ______  _    _ _____ _          _____ _____  
       /\  |  ___ \| |  | (_____) |        (_____) ___ \ 
      /  \ | |   | | |  | |  _  | |           _ | |   | |
     / /\ \| |   | |\ \/ /  | | | |          | || |   | |
    | |__| | |   | | \  /  _| |_| |_____    _| || |___| |
    |______|_|   |_|  \/  (_____)_______)  (_____)_____/

        ''')
    print("##########################################################")
    
    # Find all game extensions, note that those folders contain game specific logic,
    # which will not be included in main anvil_io project
    extensions = [ext for ext in os.listdir(EXTENSIONS_PATH) if os.path.isdir(os.path.join(EXTENSIONS_PATH, ext))]
    log("main", "Found game extensions", extensions)    
    log("main", "Enabled game extensions", ENABLED_ZONES)
    
    

if __name__ == "__main__":
    launch() # execute only if run as a script