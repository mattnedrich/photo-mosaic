import os
import sys
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from PIL import Image

from config import get_config
from img_util import partition_image_and_sum_grid_cells

def get_image_color_distribution(img, CONFIG):
  data = np.asarray(img, dtype='int32')
  grids = CONFIG['binsPerTile']
  
  assert data.shape[0] == data.shape[1]
  assert data.shape[2] == 3
  assert data.shape[0] % grids == 0

  grid_size = int(data.shape[0] / grids)

  red = data[...,0]
  green = data[...,1]
  blue = data[...,2]

  red_data = partition_image_and_sum_grid_cells(red, grid_size)
  green_data = partition_image_and_sum_grid_cells(green, grid_size)
  blue_data = partition_image_and_sum_grid_cells(blue, grid_size)

  return {
    'red': red_data,
    'green': green_data,
    'blue': blue_data
  }
  

def run():
  CONFIG = get_config()
  TILE_PATH = CONFIG['tilePath']

  tiles = [f for f in os.listdir(TILE_PATH) if os.path.isfile(os.path.join(CONFIG['photoPath'], f)) and f.endswith('.jpeg')]
  library = []
  for idx, tile in enumerate(tiles):
    img_path = os.path.join(TILE_PATH, tile)
    img = Image.open(img_path)
    img.load()
    result = {}
    result['id'] = tile
    result['path'] = img_path
    result = {**result, **get_image_color_distribution(img, CONFIG)}
    library.append(result)
    if idx % 100 == 0:
      print(f'completed {idx} of {len(tiles)}')

  with open('output/index.json', 'w') as f:
    json.dump(library, f, default=str)

if __name__ == '__main__':
  run()