import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cropper import crop
from config import get_config
from os import listdir
from os.path import isfile, join

def run():
  CONFIG = get_config()
  TILE_SIZE = int(CONFIG['tileSizeInPixels'])

  files = [f for f in listdir(CONFIG['photoPath']) if isfile(join(CONFIG['photoPath'], f)) and f.endswith('.jpeg')]
  for f in files:
    img_path = os.path.join(CONFIG['photoPath'], f)
    crop(img_path, CONFIG['tilePath'], TILE_SIZE)

if __name__ == "__main__":
  run()