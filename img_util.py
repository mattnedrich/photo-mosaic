import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# from: https://stackoverflow.com/a/16873755/1753703
def blockshaped(arr, nrows, ncols):
    """
    Return an array of shape (n, nrows, ncols) where
    n * nrows * ncols = arr.size

    If arr is a 2D array, the returned array looks like n subblocks with
    each subblock preserving the "physical" layout of arr.
    """
    h, w = arr.shape
    assert h % nrows == 0, f"{h} rows is not evenly divisible by {nrows}"
    assert w % ncols == 0, f"{w} cols is not evenly divisible by {ncols}"
    return (arr.reshape(h//nrows, nrows, -1, ncols)
               .swapaxes(1,2)
               .reshape(-1, nrows, ncols))

def partition_image(img, rows, cols):
  return blockshaped(img, rows, cols)

def partition_image_and_sum_grid_cells(img, n):
  # splits an image into an nxn grid and sums the color values of each grid cell

  # make sure the image is evenly divisible into an nxn grid  
  assert img.shape[0] == img.shape[1]
  assert img.shape[0] % n == 0

  chunks = blockshaped(img, n, n)
  sums = []
  
  for c in range(chunks.shape[0]):
    sums.append(chunks[c].sum())
  return sums