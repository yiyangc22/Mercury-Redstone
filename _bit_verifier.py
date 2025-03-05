"""bit scheme generator prototype (from _bit_prototype.ipynb)"""

import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image


def get_csv(dirc):
    """
    Function: return the content of a designated .csv file in a 2d list.
    """
    rtn = []
    loc = pd.read_csv(dirc, keep_default_na=False).values.tolist()
    for row in enumerate(loc):
        rtn.append(row[1][1:])
    return rtn


def pyplot_create_region(
        x: float,       # center x coordinate                       float / int
        y: float,       # center y coordinate                       float / int
        w: float,       # size of FOV over x axis                   float / int
        h: float,       # size of FOV over y axis                   float / int
        c = 'b',        # color to be used to plot the center       str / chr
        e = 'b',        # color to be used to plot the border       str / chr
        f = 'left',     # alignment of the center i to x axis       str / chr
        v = 'top',      # alignment of the center i to y axis       str / chr
        i = "",         # value to be displayed at the center       (printable)
        j = "",         # image to be displayed at the center       (file path)
        a = 1,          # alpha value of all marking elements       float / int
        b = False,      # flip image horizontally                   bool
        d = False,      # flip image vertically                     bool
        r = 0,          # counter-clockwise rotational angles       int
        t = 0,          # counter-clockwise rotation for text       int
):
    """
    ### Store a rectangle with width = w and height = h at (x,y), marked with i.
    
    `x` : center x coordinate.
    `y` : center y coordinate.
    `w` : size of FOV over x axis.
    `h` : size of FOV over y axis.
    -----------------------------------------------------------------------------------------------
    #### Optional:
    `c` : color to be used to plot the center. Default = `'b'` *(blue)*.
    `e` : color to be used to plot the border. Default = `'b'` *(blue)*.
    `f` : alignment of the center i to x axis. Default = `'left'`.
    `v` : alignment of the center i to y axis. Default = `'top'`.
    `i` : value to be displayed at the center. Default = `""`.
    `j` : image to be displayed at the center. Default = `""`.
    `a` : alpha value of all marking elements. Default = `1`.
    `b` : flip image horizontally if True. Default = `False`.
    `d` : flip image vertically if True. Default = `False`.
    `r` : counter-clockwise rotational angles. Default = `0`.
    `t` : counter-clockwise rotation for text. Default = `0`.
    """
    # declare two lists to store corner coordinates
    corner_x = []
    corner_y = []
    # bottom left (start)
    corner_x.append(x - 0.5*w)
    corner_y.append(y - 0.5*h)
    # top left
    corner_x.append(x - 0.5*w)
    corner_y.append(y + 0.5*h)
    # top right
    corner_x.append(x + 0.5*w)
    corner_y.append(y + 0.5*h)
    # bottom right
    corner_x.append(x + 0.5*w)
    corner_y.append(y - 0.5*h)
    # bottom left (finish)
    corner_x.append(x - 0.5*w)
    corner_y.append(y - 0.5*h)
    # plot i as label
    plt.plot(x, y, 'o', color=c, alpha=a)
    plt.text(x, y, i, ha=f, va=v, alpha=1, rotation=t)
    # plot j as image and rectX - rectY as lines
    if j != "":
        # open image with PIL
        img = Image.open(j)
        # flip or rotate the image if needed
        if b is True:
            img = img.transpose(method=Image.Transpose.FLIP_LEFT_RIGHT)
        if d is True:
            img = img.transpose(method=Image.Transpose.FLIP_TOP_BOTTOM)
        if r != 0:
            img = img.rotate(r)
        # store img, stretch its dimension to fit the current FOV
        ax = plt.gca()
        ax.imshow(np.fliplr(np.flipud(img)), extent=(x+0.5*w, x-0.5*w, y+0.5*h, y-0.5*h))
        # invert the axes back as imshow will invert x and y axis
        ax.invert_xaxis()
        ax.invert_yaxis()
        # graph rectX - recty with linestyle ':'
        plt.plot(corner_x, corner_y, ':', color=e, alpha=a)
    else:
        # graph rectX - recty with linestyle '-'
        plt.plot(corner_x, corner_y, '-', color=e, alpha=a)

# default experiment folder
EXP_FOLDER_PATH = os.path.join(os.path.expanduser("~"), "Desktop", "_latest")

# default cleave cycle export path
EXP_LASER_CYCLE = os.path.join(EXP_FOLDER_PATH, "_cleave_cycle.csv")

# default area size (um/IU)
BIT_IMAGE_SIZES = [366,366]

# extract cleave cycle data
BIT_LASER_CYCLE = get_csv(EXP_LASER_CYCLE)

# reconstruct original bit schemes
image_scheme = []
for command in BIT_LASER_CYCLE:
    _ = True
    for image in image_scheme:
        if image[3] == command[3]:
            _ = False
            image[4].append(command[4])
            break
    if _ is True:
        image_scheme.append([command[0], command[1], command[2], command[3], [command[4]]])

# # print reconstructed bit sequence
# for image in image_scheme:
#     print(image[4])

time_complexity = 0
current_port = BIT_LASER_CYCLE[0][4]
for i, entry in enumerate(BIT_LASER_CYCLE):
    time_complexity += 5
    if current_port != entry[4]:
        current_port = entry[4]
        time_complexity += 60*4 + 900
print(time_complexity/60)

# store preview for the bit scheme
for area in image_scheme:
    pyplot_create_region(
        x = area[0],
        y = area[1],
        w = BIT_IMAGE_SIZES[0],
        h = BIT_IMAGE_SIZES[1],
        f = 'center',
        v = 'center',
        i = area[4],
        a = 0.25,
        t = -45
    )
plt.gca().set_aspect('equal')
plt.gcf().set_figwidth(15)
plt.gcf().set_figheight(7.5)
plt.tight_layout()
plt.show()
