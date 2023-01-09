import os
# import json
import smartcrop

from PIL import Image

# def face_detection(src_path):
#   print(src_path)
#   image = face_recognition.load_image_file(src_path)
#   face_locations = face_recognition.face_locations(image)
#   print(face_locations)

def downsample_image(img, tile_size):
  width, height = img.size
  smallest_dimension = min(width, height)
  downsample_ratio = smallest_dimension / tile_size

  new_width = int(width / downsample_ratio)
  new_height = int(height / downsample_ratio)

  new_image = img.resize((new_width, new_height), Image.ANTIALIAS)
  return new_image

def crop(src_path, output_dir, tile_size):
  filename = os.path.basename(src_path)
  image = Image.open(src_path)

  resized_image = downsample_image(image, tile_size)

  sc = smartcrop.SmartCrop()
  result = sc.crop(resized_image, tile_size, tile_size)
  # print(result)
  box = (
        result['top_crop']['x'],
        result['top_crop']['y'],
        result['top_crop']['width'] + result['top_crop']['x'],
        result['top_crop']['height'] + result['top_crop']['y']
    )
  # print(box)

  cropped_image = resized_image.crop(box)
  cropped_image.save(os.path.join(output_dir, filename))
