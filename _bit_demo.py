"""bit system: concept demo (10x10, 366IU, 20 ports)"""

import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image

###################################################################################################
#                                      INDEPENDENT FUNCTIONS                                      #    

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


def get_csv(dirc):
    """
    Function: return the content of a designated .csv file in a 2d list.
    """
    rtn = []
    loc = pd.read_csv(dirc, keep_default_na=False).values.tolist()
    for row in enumerate(loc):
        rtn.append(row[1][1:])
    return rtn

#                                      INDEPENDENT FUNCTIONS                                      #
###################################################################################################


###################################################################################################
#                                       CONSTANT PARAMETERS                                       #

# default experiment folder
EXP_FOLDER_PATH = os.path.join(os.path.expanduser("~"), "Desktop", "_latest")

# default coordinate file location
EXP_COORDINATES = os.path.join(EXP_FOLDER_PATH, "_coordinates.csv")

# default cleave cycle export path
EXP_LASER_CYCLE = os.path.join(EXP_FOLDER_PATH, "_cleave_cycle.csv")

# default laser mask file location
EXP_MASK_FOLDER = os.path.join(EXP_FOLDER_PATH, "Subgroup 1")

# default laser mask naming scheme
EXP_MASK_STARTS = 1000
EXP_MASK_TRAILS = "_MC_F001_Z001.png"

# xyz list of barcode images/areas
BIT_COORDINATES = get_csv(EXP_COORDINATES)
BIT_IMAGE_SIZES = [366,366]

# number of images/areas to barcode
BIT_NUM_OF_AREA = len(BIT_COORDINATES)

# list of flow ports for each oligo
BIT_OLIGO_PORTS = [ 1, 2, 3, 4, 5, 6, 7, 8, 9,10,   11,12,13,14,15,16,17,18,19,21 ]
BIT_OLIGO_ASSGN = [[1, 2, 3, 4, 5, 6, 7, 8, 9,10], [11,12,13,14,15,16,17,18,19,21]]
BIT_OLIGO_INDEX = [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [10,11,12,13,14,15,16,17,18,19]]

#                                       CONSTANT PARAMETERS                                       #
###################################################################################################


###################################################################################################
#                                            MAIN BODY                                            #

# predict mask file names based on naming scheme
mask_sequences = []
for i in range(BIT_NUM_OF_AREA):
    mask_sequences.append(str(EXP_MASK_STARTS+i)+EXP_MASK_TRAILS)

# merge coordinate list with predicted mask list
merged_list = BIT_COORDINATES
for i, coordinate in enumerate(merged_list):
    coordinate.append(mask_sequences[i])

# generate fluidic scheme for the merged list
first_set = BIT_OLIGO_ASSGN[0]
second_set = BIT_OLIGO_ASSGN[1]
unique_sequences = []
for second_digit in second_set:
    for first_digit in first_set:
        unique_sequences.append([first_digit, second_digit])

# use the bit scheme to map fluidic command
fluidic_scheme = []
for i in range(len(unique_sequences[0])):
    for port in BIT_OLIGO_PORTS:
        for j, sequence in enumerate(unique_sequences):
            if sequence[i] == port:
                temp = merged_list[j][:]
                temp.append(port)
                fluidic_scheme.append(temp)
print(fluidic_scheme)

# save the new fluidic scheme to a new file
dataframe = pd.DataFrame(fluidic_scheme, columns=['x','y','z','mask','port'])
dataframe.to_csv(EXP_LASER_CYCLE, index=True)

# reconstruct original bit schemes
BIT_LASER_CYCLE = get_csv(EXP_LASER_CYCLE)
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

# calculate time complexity of the current scheme
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

#                                            MAIN BODY                                            #
###################################################################################################
