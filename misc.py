import logging
import os
import sys
try:
    from yaml import load, dump
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

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