import os
import json
def getSysConfig():
    data = None
    DB_SECRET_FILE = 'sysConfig.json'
    if True == os.path.exists(DB_SECRET_FILE):
        with open(DB_SECRET_FILE) as json_file:
            data = json.load(json_file)
    return data