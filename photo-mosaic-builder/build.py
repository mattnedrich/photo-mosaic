import os
import sys
import math
import json 
import time
import shutil

import numpy as np
from PIL import Image
from scipy.optimize import linear_sum_assignment

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

# def find_best_match(library, target_red, target_green, target_blue, history):
#   closest = None
#   closest_dist = float('inf')
#   for entry in library:
#     dist_r = vector_distance(target_red, entry['red'])
#     dist_g = vector_distance(target_green, entry['green'])
#     dist_b = vector_distance(target_blue, entry['blue'])
#     dist_total = dist_r + dist_g + dist_b
#     if dist_total < closest_dist:
#       closest = entry
#       closest_dist = dist_total
#   return closest

def compute_all_costs(library, target_red, target_green, target_blue):
  costs = []
  # vectorize to speed up
  for entry in library:
    dist_r = vector_distance(target_red, entry['red'])
    dist_g = vector_distance(target_green, entry['green'])
    dist_b = vector_distance(target_blue, entry['blue'])
    dist_total = dist_r + dist_g + dist_b
    costs.append(dist_total)
  return costs 

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

def build_repeats(data, count, penalty):
  result = data 
  for i in range(count):
    result = result + [((1+ (penalty * i)) * d) for d in data]
  return result

def build_mosaic(data, tile_size, cell_bins, library, num_repeats, repeat_penalty, blend_with_source, blend_ratio, src_img):
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


  # ideas:
  # pre-process one iteration and cache coord, and rgb values, then iterate over some number
  # of iterations to find the best match, subject to some constraint. Consider hugarian alg.

  target_image_data = {}
  grid_size = int(tile_size / cell_bins)
  for idx, (r, g, b) in enumerate(zip(superpixels_red, superpixels_green, superpixels_blue)):
    coord = get_image_location(idx, num_rows, num_cols, tile_size)
    values_red = partition_image_and_sum_grid_cells(r, grid_size)
    values_green = partition_image_and_sum_grid_cells(g, grid_size)
    values_blue = partition_image_and_sum_grid_cells(b, grid_size)
    target_image_data[idx] = {}
    target_image_data[idx]['coord'] = coord
    target_image_data[idx]['red'] = values_red
    target_image_data[idx]['green'] = values_green
    target_image_data[idx]['blue'] = values_blue

  tile_infos = []
  cost_matrix = []
  for idx, (r, g, b) in enumerate(zip(superpixels_red, superpixels_green, superpixels_blue)):
    print(f'processing super pixel {idx} of {len(superpixels_red)}')
    target = target_image_data[idx]
    # best_match = find_best_match(library, target['red'], target['green'], target['blue'], history)
    costs_for_idx = compute_all_costs(library, target['red'], target['green'], target['blue'])

    if num_repeats > 0:
      costs_for_idx_with_repeats = build_repeats(costs_for_idx, num_repeats, repeat_penalty)
      cost_matrix.append(costs_for_idx_with_repeats)
    else:
      cost_matrix.append(costs_for_idx)

    tile_infos.append({
      'index': idx,
      'coord': target['coord']
    })

  row_ind, col_ind = linear_sum_assignment(cost_matrix)
  
  mosaic_output = Image.new('RGB', (num_cols * tile_size, num_rows * tile_size), color='pink')
  for tile in tile_infos:
    best_fit_index = col_ind[tile['index']]
    best_fit = library[best_fit_index % len(library)]
    write_tile(mosaic_output, best_fit, tile['coord'])

  if blend_with_source:
    # import pdb
    # pdb.set_trace()
    if src_img.mode == 'RGBA':
      src_img = Image.alpha_composite(Image.new('RGBA', src_img.size, (255, 255, 255)), src_img).convert('RGB')
    blended_mosaic = Image.blend(mosaic_output, src_img, blend_ratio)
    return blended_mosaic
  else:
    return mosaic_output

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

  return [mosaic_img, data_crop]

def handle_int64_strings(obj):
  new_obj = obj
  new_obj['red'] = [int(val) for val in obj['red']]
  new_obj['green'] = [int(val) for val in obj['green']]
  new_obj['blue'] = [int(val) for val in obj['blue']]
  return new_obj

def run_one_image(source_path, CONFIG):
  tile_size = CONFIG['tileSizeInPixels']
  cell_bins = CONFIG['binsPerTile']
  num_repeats = CONFIG['mosaicNumRepeats']
  repeat_penalty = CONFIG['mosaicRepeatPenalty']
  cell_bins = CONFIG['binsPerTile']
  blend_with_source = CONFIG['mosaicBlendWithSource']
  blend_ratio = CONFIG['mosaicBlendRatio']
  src_img, img_data = prepare_mosaic(source_path, tile_size)

  with open('output/index.json') as f:
    library = json.load(f, object_hook=handle_int64_strings)
  mosaic = build_mosaic(img_data, tile_size, cell_bins, library, num_repeats, repeat_penalty, blend_with_source, blend_ratio, src_img)
  epoch_time = int(time.time())
  source_filename = os.path.basename(source_path).split('.')[0]
  output_dir = f'{source_filename}-{epoch_time}'

  os.makedirs(f'output/{output_dir}')
  mosaic.save(f'output/{output_dir}/mosaic.png')
  shutil.copyfile('config.json', f'output/{output_dir}/config.json')

def run():
  CONFIG = get_config()
  source_path = CONFIG['mosaicSourcePath']

  if os.path.isdir(source_path):
    images = [f for f in os.listdir(source_path) if os.path.isfile(os.path.join(CONFIG['photoPath'], f)) and f.endswith('.jpeg')]
    for idx, tile in enumerate(images):
      print(f'processing image {idx} of {len(images)}')
      img_path = os.path.join(source_path, tile)
      run_one_image(img_path, CONFIG)
  else:
    run_one_image(source_path, CONFIG)
    pass

if __name__ == '__main__':
  run()