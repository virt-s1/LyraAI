import csv
import logging
import os
import sys
try:
    from yaml import load, dump
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from filelock import FileLock
from typing import List

def param_init(cfg_file = None):
    # Config file
    if not cfg_file:
        cfg_file = 'settings.yaml'
    
    print("load/update params from {}".format(cfg_file))
    if not os.path.exists(cfg_file):
        print("{} config file not found!".format(cfg_file))
        sys.exit(1)
    keys_data = None
    try:
        if cfg_file:
            with open(cfg_file,'r') as fh:
                keys_data = load(fh, Loader=Loader)
            return keys_data
    except Exception as err:
        print(err)
    return keys_data

# save data to csv file
def save_data_csv(csv_file: str=None, headers: List[str]=None, data: List[dict]=None)->bool:
    with FileLock(csv_file + '.lock'):
        if not os.path.exists(csv_file):
            with open(csv_file, 'w+') as fh:
                csv_data = csv.DictWriter(fh, headers)
                csv_data.writeheader()
        with open(csv_file, 'a+') as fh:
            csv_data = csv.DictWriter(fh, headers)
            csv_data.writerows(data)
    return True