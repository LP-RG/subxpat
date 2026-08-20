"""
    @authors: Ilia Zeller
"""

from PIL import Image
import os
import math

files = sorted(os.listdir("individual_circuits_plots"), key=lambda s: (sum(c.isalpha() for c in s), s))
files = sorted(files, key=len)

images = [Image.open("individual_circuits_plots/" + x) 
          for x in files
          if x != "merged_plots.png"]
widths, heights = zip(*(i.size for i in images))

max_width = max(widths)
max_height = max(heights)

new_im = Image.new('RGB', (int(max_width * 4), max_height*(math.ceil(len(images)/4))))

x_offset = 0
ctr = 0
for im in images:
  if ctr < 4:
    new_im.paste(im, (x_offset,0))
  elif ctr == 4:
    x_offset = 0
    new_im.paste(im, (x_offset, max_height))
  else:
    new_im.paste(im, (x_offset, max_height))
  x_offset += im.size[0]
  ctr += 1

new_im.save('individual_circuits_plots/merged_plots.png')