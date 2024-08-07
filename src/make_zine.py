#!/usr/bin/env python

""" Gimp plugin to create a single sheet zine.

License https://opensource.org/license/mit/
Copyright 2024 Steve Butler (henspace.com).

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the 'Software'), to deal in
the Software without restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the
Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
"""

from gimpfu import *
import os
import re
import math



def showUsage(summary):
  """ Display a message using the dialog box message handler.

  Displays a message using a dialog box. The summary is displayed first followed
  by detailed usage information.

  Args:
    summary: brief text displayed as a single line at the top of the message.
  """

  usageMsg = ("The filename of your working file must be of the " +
  "form name0.png, or any other file type Gimp can handle. The script will " +
  "then look for images in the same folder with the names 'name0.ext' to " +
  "'name7.ext' to form the pages of the zine. The 'name' can be anything " +
  "and 'ext' will match the extension of the working file.")
  messageHandler = pdb.gimp_message_get_handler()
  pdb.gimp_message_set_handler(0) # MESSAGE BOX
  pdb.gimp_message(summary + "\n\n" + usageMsg)
  pdb.gimp_message_set_handler(messageHandler)

def makezine(image, drawable, greyscale, dpi, useMM, pageWidth, pageHeight, panelMargin): 
  """ Main entry point for the plugin.

  Creates a zine using information from the current working image.

  Args:
    image: the working image passed in via the Gimp plugin handler.
    drawable: the working drawable object passed in via the Gimp plugin handler.
    greyscale: boolean. 
    dpi: integer.
    useMM: boolean. If true, dimensions are taken as mm, otherwise they are assumed to be inches.
    pageWidth: width of the output page.
    pageHeight: height of the output page.
    panelMargin: margin. This applies to all panels.
  """
  pdb.gimp_message_set_handler(1) # Messages to the console
  filename = pdb.gimp_image_get_filename(image)
  if filename is None:
    showUsage("No image to work on.")
    return
  (filename, ext) = os.path.splitext(filename)
  rootName = re.sub("0$", "", filename)
  if rootName == filename:
    showUsage("You must be working on page 0 (cover) to create the zine.")
    return
  pdb.gimp_message("Working on file %s; extension %s; root %s" % (filename, ext, rootName))
  # set up dimensions in inches
  if useMM:
    pageWidthInches = pageWidth / 25.4
    pageHeightInches = pageHeight / 25.4
    panelMarginInches = panelMargin / 25.4
  else:
    pageWidthInches = pageWidth
    pageHeightInches = pageHeight
    panelMarginInches = panelMargin
  
  if (pageWidthInches < pageHeightInches):
    # force landscape
    temp = pageWidthInches
    pageWidthInches = pageHeightInches
    pageHeightInches = temp

  
  
  # set up page dimensions
  pageWidthPx = round(pageWidthInches * dpi)
  pageHeightPx = round(pageHeightInches * dpi)
  marginPx = round(panelMarginInches * dpi)

  # create image
  if greyscale:
    imageType = 1 # GRAY
    layerType = 3 # GRAYA-IMAGE
  else:
    imageType = 0 # RGB
    layerType = 1 # RGBA_IMAGE
  zineImage = pdb.gimp_image_new(pageWidthPx, pageHeightPx , imageType)
  
  # set up panel dimensions. Note the terms width and height are relative to the
  # panel, not the page.
  panelHeightPx = 0.5 * pageHeightPx
  panelWidthPx = 0.25 * pageWidthPx
  innerPanelHeightWholePx = round(panelHeightPx - 2 * marginPx)
  innerPanelWidthWholePx = round(panelWidthPx - 2 * marginPx)
  innerAspectRatio = float(innerPanelWidthWholePx) / innerPanelHeightWholePx

  # panel offsets in panels in x direction, panels in y direction and a boolean
  # indicating whether the image is rotated 180 degrees.
  panelOffsets = [
    (2, 0, True),
    (1, 0, True),
    (0, 0, True),
    (0, 1, False),
    (1, 1, False),
    (2, 1, False),
    (3, 1, False), 
    (3, 0, True)
  ]
  panelGroup = pdb.gimp_layer_group_new(zineImage)
  pdb.gimp_item_set_name(panelGroup, 'panels')
  pdb.gimp_image_insert_layer(zineImage, panelGroup, pdb.gimp_image_get_active_layer(zineImage), 0)
  for pageIndex in range(8):
    panelImageFilename = rootName + str(pageIndex) + ext
    pdb.gimp_message("Loading " + panelImageFilename)
    try:
      layer = pdb.gimp_file_load_layer(zineImage, panelImageFilename)
      pdb.gimp_item_set_name(layer, "mini-panel-" + str(pageIndex))
      aspectRatio = float(layer.width) / layer.height
      pdb.gimp_message("Dimensions %d x %d; aspect ratio %0.2f" % (layer.width, layer.height, aspectRatio))
      if aspectRatio > innerAspectRatio:
        panelImageWidthWholePx = innerPanelWidthWholePx
        panelImageHeightWholePx = round(float(layer.height) * panelImageWidthWholePx / layer.width)
      else:
        panelImageHeightWholePx = innerPanelHeightWholePx
        panelImageWidthWholePx = round(float(layer.width) * panelImageHeightWholePx / layer.height)

      pdb.gimp_image_insert_layer(zineImage, layer, panelGroup, 0)
      pdb.gimp_context_set_interpolation(2) # cubic
      pdb.gimp_layer_scale(layer, panelImageWidthWholePx, panelImageHeightWholePx, False)
      offsets = panelOffsets[pageIndex]
      if offsets[2]:
        pdb.gimp_item_transform_flip_simple(layer, 0, True, 0) # horizontal
        pdb.gimp_item_transform_flip_simple(layer, 1, True, 0) # vertical
      offsetX = round(offsets[0] * panelWidthPx + 0.5 * (panelWidthPx - panelImageWidthWholePx))
      offsetY = round(offsets[1] * panelHeightPx + 0.5 * (panelHeightPx - panelImageHeightWholePx) )
      pdb.gimp_layer_set_offsets(layer, offsetX, offsetY)
    except:
      pdb.gimp_message("Panel image %s not found." % (panelImageFilename))
  display = pdb.gimp_display_new(zineImage)

# Register the script
register(
  "python_fu_makezine",
  "Zine maker",
  "Layout images to make zine",
  "Steve Butler",
  "Steve Butler",
  "2024",
  "<Image>/Image/Make zine...",
  "*",
  [
    (PF_BOOL, "greyscale", "Grey scale", True),
    (PF_INT, "dpi", "DPI", 600),
    (PF_BOOL, "useMM", "Dims in mm (otherwise inches)", True),
    (PF_FLOAT, "pageWidth", "Page width", 210),
    (PF_FLOAT, "pageHeight", "Page height", 297),
    (PF_FLOAT, "panelMargin", "Page margin", 5),
  ],
  [],
  makezine
  )

main()
