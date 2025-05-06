"""bit system: scheme generator prototype"""

import os
from itertools import product

import pandas as pd


###################################################################################################
#                                      INDEPENDENT FUNCTIONS                                      #

def generate_digit_sequences():
    num_images = 100
    num_digits = 20
    first_set = list(range(10))  # Digits 0-9
    second_set = list(range(10, 20))  # Digits 10-19
    
    length = 2  # Fixed length for each sequence (alternating digits)
    unique_sequences = []
    
    for second_digit in second_set:
        for first_digit in first_set:
            unique_sequences.append([first_digit, second_digit])
            if len(unique_sequences) == num_images:
                return unique_sequences
    
    return unique_sequences


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
EXP_MASK_TRAILS = "_F001_Z001.png"

# xyz list of barcode images/areas
BIT_COORDINATES = get_csv(EXP_COORDINATES)

# number of images/areas to barcode
BIT_NUM_OF_AREA = len(BIT_COORDINATES)

# number of unique oligos avaliable
BIT_NUM_MARKERS = 2

# list of flow ports for each oligo
BIT_OLIGO_PORTS = [1, 2, 3, 4, 5, 6, 9,10,11,12,13,14,15,16,17,18,19,21]
BIT_OLIGO_INDEX = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9,10,11,12,13,14,15,16,17]

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

# generate a bit scheme for each mask image
bit_sequences = generate_digit_sequences(BIT_NUM_OF_AREA, BIT_NUM_MARKERS)

# replace bit scheme notations with port numbers
for sequence in bit_sequences:
    for bit in sequence:
        if bit != 0:
            bit = BIT_OLIGO_PORTS[bit - 1]

# use the bit scheme to map fluidic command
fluidic_scheme = []
for i in range(len(bit_sequences[0])):
    for port in BIT_OLIGO_PORTS:
        for j, sequence in enumerate(bit_sequences):
            if sequence[i] == port:
                temp = merged_list[j][:]
                temp.append(port)
                fluidic_scheme.append(temp)

# save the new fluidic scheme to a new file
dataframe = pd.DataFrame(fluidic_scheme, columns=['x','y','z','mask','port'])
dataframe.to_csv(EXP_LASER_CYCLE, index=True)

#                                            MAIN BODY                                            #
###################################################################################################
