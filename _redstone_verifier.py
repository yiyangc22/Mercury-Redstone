"""bit system: cleave cycle file verifier prototype"""

import os

import matplotlib.pyplot as plt

from _redstone_generator import get_csv
from mercury_01 import pyplot_create_region


###################################################################################################
#                                       CONSTANT PARAMETERS                                       #

# default experiment folder
EXP_FOLDER_PATH = os.path.join(os.path.expanduser("~"), "Desktop", "_latest")

# default cleave cycle export path
EXP_LASER_CYCLE = os.path.join(EXP_FOLDER_PATH, "_cleave_cycle.csv")

# default area size (um/IU)
BIT_IMAGE_SIZES = [366,366]

# extract cleave cycle data
BIT_LASER_CYCLE = get_csv(EXP_LASER_CYCLE)

#                                       CONSTANT PARAMETERS                                       #
###################################################################################################


###################################################################################################
#                                            MAIN BODY                                            #

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

# store preview for the bit scheme
for area in image_scheme:
    pyplot_create_region(
        x = area[0],
        y = area[1],
        w = BIT_IMAGE_SIZES[0],
        h = BIT_IMAGE_SIZES[1],
        i = area[4]
    )
plt.gca().set_aspect('equal')
plt.gcf().set_figwidth(15)
plt.gcf().set_figheight(7.5)
plt.tight_layout()
plt.show()

#                                            MAIN BODY                                            #
###################################################################################################
