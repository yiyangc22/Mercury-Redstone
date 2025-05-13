"""
Mercury 02: laser scheme constructor, project version 1.2 (with python 3.9).
"""

import os
import tkinter as tk
from itertools import product
import customtkinter
import pandas as pd
import matplotlib.pyplot as plt
from mercury_01 import pyplot_create_region
from mercury_03 import get_csv

WINDOW_TXT = "Mercury II - Laser Scheme Constructor"
WINDOW_RES = "900x100"
PARAMS_EXP = os.path.join(os.path.expanduser("~"), "Desktop", "_latest")


# ===================================== customtkinter classes =====================================

class App(customtkinter.CTk):
    """
    Class: main application window and customtkinter main loop.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self):
        super().__init__()
        # ---------------------------------- application setting ----------------------------------
        self.title(WINDOW_TXT)
        self.geometry(WINDOW_RES)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        # -------------------------------------- GUI setting --------------------------------------
        self.frm_ctl = Exp(master=self)
        self.frm_ctl.grid(row=0, column=0, padx=10, pady=(10,5), sticky="nesw", columnspan=1)
        self.btn_cmc = customtkinter.CTkButton(master=self, text="Commence", command=self.app_exp)
        self.btn_cmc.grid(row=1, column=0, padx=10, pady=(5,10), sticky="nesw", columnspan=1)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on call ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def app_exp(self):
        """
        Function: commence the export of collected user inputs.
        """
        # experiment folder
        EXP_FOLDER_PATH = self.frm_ctl.ent_pth.get()
        # coordinate file location
        EXP_COORDINATES = os.path.join(EXP_FOLDER_PATH, "_coordinates.csv")
        # cleave cycle export path
        EXP_LASER_CYCLE = os.path.join(EXP_FOLDER_PATH, "_cleave_cycle.csv")
        EXP_BIT_STRINGS = os.path.join(EXP_FOLDER_PATH, "_bit_string.csv")
        # laser mask file location
        EXP_MASK_FOLDER = os.path.join(EXP_FOLDER_PATH, "Mask Images")
        # laser mask naming scheme
        EXP_MASK_STARTS = 1000
        EXP_MASK_TRAILS = "_MC_F001_Z001.png"
        # xyz list of barcode images/areas
        BIT_COORDINATES = get_csv(EXP_COORDINATES)
        # number of images/areas to barcode
        BIT_NUM_OF_AREA = len(BIT_COORDINATES)
        # number of unique oligos avaliable
        BIT_NUM_MARKERS = 20
        # default area size (um/IU)
        BIT_IMAGE_SIZES = [366,366]
        # list of flow ports for each oligo
        BIT_OLIGO_PORTS = [1, 2, 3, 4, 5, 6, 7, 8, 9,10,11,12,13,14,15,16,17,18,19,21]
        BIT_OLIGO_INDEX = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9,10,11,12,13,14,15,16,17,18,19]
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
            for i, bit in enumerate(sequence):
                sequence[i] = BIT_OLIGO_PORTS[bit]
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
        # extract cleave cycle data
        BIT_LASER_CYCLE = get_csv(EXP_LASER_CYCLE)
        # list all masks without repeating
        image_scheme = []
        for command in BIT_LASER_CYCLE:
            appending = True
            for image in image_scheme:
                if image[3] == command[3]:
                    appending = False
            if appending:
                image_scheme.append([command[0], command[1], command[2], command[3], []])
        # reconstruct original bit schemes
        for image in image_scheme:
            for command in BIT_LASER_CYCLE:
                if command[3] == image[3]:
                    image[4].append(command[4])
        # read folder, save image paths in list, and print
        masks = []
        for file in os.listdir(EXP_MASK_FOLDER):
            if file[-len(EXP_MASK_TRAILS):] == EXP_MASK_TRAILS:
                masks.append(os.path.join(EXP_MASK_FOLDER, file))
        # make a separate csv file for bit string storages
        df = pd.DataFrame({'x':[], 'y':[], 'z':[], 'mask':[], 'bit-string':[]})
        df.to_csv(EXP_BIT_STRINGS)
        # store preview for the bit scheme, save bit strings in csv file
        for i, area in enumerate(image_scheme):
            pyplot_create_region(
                x = area[0],
                y = area[1],
                w = (BIT_IMAGE_SIZES[0] * (1906/2304)),
                h = (BIT_IMAGE_SIZES[1] * (2270/2304)),
                f = 'center',
                v = 'center',
                i = area[4],
                j = masks[i],
                a = 0.2,
                b = True,
                r = 90,
                t = -45
            )
            # format bit string and save in csv file
            df1 = pd.read_csv(EXP_BIT_STRINGS)
            df2 = pd.DataFrame({
                "x": [area[0]],
                "y": [area[1]],
                "z": [area[2]],
                "mask": [area[3]],
                "bit-string": [str(area[4])]
            })
            if df1.empty:
                df1 = df2
            else:
                df1 = pd.concat([df1, df2], ignore_index=True)
            df1.to_csv(EXP_BIT_STRINGS, index=False)
        plt.gca().set_aspect('equal')
        plt.gcf().set_figwidth(15)
        plt.gcf().set_figheight(7.5)
        plt.tight_layout()
        plt.show()
        # quit customtkinter app after the preview is done
        self.quit()


class Exp(customtkinter.CTkFrame):
    """
    Class: ctk frame for adding individual instrument commands.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        # -------------------------------------- GUI setting --------------------------------------
        # create file path entry and label
        self.lbl_pth = customtkinter.CTkLabel(
            master = self,
            width = 200,
            height = 28,
            text = "Experiment Folder Path:"
        )
        self.lbl_pth.grid(row=0, column=0, padx=(10,0), pady=5, sticky="nsew")
        self.ent_pth = customtkinter.CTkEntry(
            master = self,
            width = 650,
            height = 28,
            textvariable = tk.StringVar(master=self, value=PARAMS_EXP)
        )
        self.ent_pth.grid(row=0, column=1, padx=(5,10), pady=5, sticky="nsew")


# ===================================== independent functions =====================================

def generate_digit_sequences(num_images, num_digits):
    """generate unique digit sequences for a given number of images"""
    length = 1
    while num_digits ** length < num_images:
        length += 1
    
    sequences = list(product(range(num_digits), repeat=length))[:num_images]
    return [list(seq) for seq in sequences]


# ========================================= main function =========================================

def mercury_02():
    """
    Main application loop of mercury 02, display constructed pyplot preview.
    """
    # set customtkinter appearance mode and color theme
    customtkinter.set_appearance_mode("dark")
    customtkinter.set_default_color_theme("blue")
    # enter main loop and return user inputs when ended
    try:
        app = App()
        app.resizable(False, False)
        app.mainloop()
    except AttributeError:
        return None
