import os
import json

dirname = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(dirname, 'config.json')

# CONFIG_PATH = './config.json'

def get_config():
  with open(CONFIG_PATH) as f:
    config = json.load(f)
    return config