# photo-mosaic

# Implementation Plan
## Data set prep
- Define a configuration file
- Given a source directory of photos, produce a cropped set of photos 

## Data set indexing
- Index the set of cropped photos
- Perhaps, do some analysis on the color distribution

## Build a mosiac
- Choose a source image
- Author a configuration file
- Build a mosaic
- Compute statistics

# Research
https://github.com/smartcrop/smartcrop.py

# Issues
M1 Mac observes a `2): Symbol not found: _jpeg_resync_to_restart` error when trying to run Pillow