import os
import sys
import math
import json 
import numpy as np
from PIL import Image

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from img_util import partition_image, partition_image_and_sum_grid_cells
from config import get_config

def vector_distance(a, b):
  assert len(a) == len(b)

  total = 0
  for i in range(len(a)):
    val_a = a[i]
    val_b = b[i]
    dist = (val_a - val_b) ** 2
    total += dist
  return math.sqrt(total)

def find_best_match(library, target_red, target_green, target_blue):
  closest = None
  closest_dist = float('inf')
  for entry in library:
    dist_r = vector_distance(target_red, entry['red'])
    dist_g = vector_distance(target_green, entry['green'])
    dist_b = vector_distance(target_blue, entry['blue'])
    dist_total = dist_r + dist_g + dist_b
    if dist_total < closest_dist:
      closest = entry
      closest_dist = dist_total
  return closest

def get_image_location2(index, num_rows, num_cols, cell_size):
  # (0,0) is the upper left of the image
  row = math.floor(index / num_rows)
  col = index % num_rows

  img_x = col * cell_size
  img_y = row * cell_size
  return (img_x, img_y)

def get_image_location(index, num_rows, num_cols, cell_size):
  # (0,0) is the upper left of the image
  row = math.floor(index / num_cols)
  col = index % num_cols

  img_x = col * cell_size
  img_y = row * cell_size

  print(f'index: {index}, row: {row} of {num_rows}, col: {col} of {num_cols}, x: {img_x}, y:{img_y}')
  return (img_x, img_y)

def write_tile(output, tile, pos):
  path = tile['path']
  img = Image.open(path)
  output.paste(img, pos)

def build_mosaic(data, tile_size, cell_bins, library):
  num_rows = int(data.shape[0] / tile_size)
  num_cols = int(data.shape[1] / tile_size)

  print(num_cols)
  print(num_rows)

  red = data[...,0]
  green = data[...,1]
  blue = data[...,2]
  superpixels_red = partition_image(red, tile_size, tile_size)
  superpixels_green = partition_image(green, tile_size, tile_size)
  superpixels_blue = partition_image(blue, tile_size, tile_size)

  output = Image.new('RGB', (num_cols * tile_size, num_rows * tile_size), color='pink')

  for idx, (r, g, b) in enumerate(zip(superpixels_red, superpixels_green, superpixels_blue)):
    coord = get_image_location(idx, num_rows, num_cols, tile_size)
    grid_size = int(tile_size / cell_bins)
    values_red = partition_image_and_sum_grid_cells(r, grid_size)
    values_green = partition_image_and_sum_grid_cells(g, grid_size)
    values_blue = partition_image_and_sum_grid_cells(b, grid_size)

    best_match = find_best_match(library, values_red, values_green, values_blue)
    # print(f"coord: {coord}, match: {best_match['id']}")
    write_tile(output, best_match, coord)
  
  return output

def prepare_mosaic(source_path, tile_size):
  img = Image.open(source_path)
  img.load()

  data_src = np.asarray(img)

  # trim some of the src image such that its width and height
  # are multiples of the mosaic tile size
  trim_x = data_src.shape[0] % tile_size
  trim_y = data_src.shape[1] % tile_size
  mosaic_width = data_src.shape[1] - trim_y
  mosaic_height = data_src.shape[0] - trim_x

  # crop target image
  mosaic_img = img.crop((0, 0, mosaic_width, mosaic_height))
  data_crop = np.asarray(mosaic_img)

  return data_crop

def handle_int64_strings(obj):
  new_obj = obj
  new_obj['red'] = [int(val) for val in obj['red']]
  new_obj['green'] = [int(val) for val in obj['green']]
  new_obj['blue'] = [int(val) for val in obj['blue']]
  return new_obj

def run():
  CONFIG = get_config()
  source_path = CONFIG['mosaicSourcePath']
  tile_size = CONFIG['tileSizeInPixels']
  cell_bins = CONFIG['binsPerTile']
  
  # crop target image into appropriate size
  img_data = prepare_mosaic(source_path, tile_size)

  with open('output/index.json') as f:
    library = json.load(f, object_hook=handle_int64_strings)
  mosaic = build_mosaic(img_data, tile_size, cell_bins, library)
  mosaic.save('output/out.png')

if __name__ == '__main__':
  run()