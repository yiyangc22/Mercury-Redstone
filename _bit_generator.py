"""bit scheme generator prototype (from _bit_prototype.ipynb)"""


import os
from itertools import product

import pandas as pd


def generate_digit_sequences(num_images, num_digits):
    """
    Function: generate unique digit sequences for a given number of images
    """
    unique_sequences = []
    length = 1

    while len(unique_sequences) < num_images:
        candidates = product(range(num_digits + 1), repeat=length)
        seen = set()
        temp_sequences = []

        for seq in candidates:
            stripped_seq = tuple(d for d in seq if d != 0)  # Remove placeholders (0s)
            if stripped_seq and stripped_seq not in seen:  # Ensure it's not empty and unique
                seen.add(stripped_seq)
                temp_sequences.append(list(seq))
            if len(temp_sequences) == num_images:
                break

        if len(temp_sequences) >= num_images:
            unique_sequences = temp_sequences[:num_images]
            break

        length += 1

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

# number of images/areas to barcode
BIT_NUM_OF_AREA = len(BIT_COORDINATES)

# number of unique oligos avaliable
BIT_NUM_MARKERS = 3

# list of flow ports for each oligo
BIT_OLIGO_PORTS = [1, 2, 3, 4, 5, 6, 9,10,11,12,13,14,15,16,17,18,19,21]
BIT_OLIGO_INDEX = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9,10,11,12,13,14,15,16,17]

# predict mask file names based on naming scheme
mask_sequences = []
for i in range(BIT_NUM_OF_AREA):
    mask_sequences.append('\\'+str(EXP_MASK_STARTS+i)+EXP_MASK_TRAILS)

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

# print generated barcoding sequence for preview
for sequence in bit_sequences:
    print(sequence)

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
