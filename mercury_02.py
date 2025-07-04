"""
Mercury 02: laser scheme constructor, project version 1.2 (with python 3.9).
"""

import os
import math
import tkinter as tk
from itertools import combinations
from datetime import date

import customtkinter
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw

from mercury_01 import pyplot_create_region, open_file_dialog
from mercury_03 import get_csv

WINDOW_TXT = "Mercury II - Laser Scheme Constructor"
WINDOW_RES = "800x190"
PARAMS_DTP = os.path.join(os.path.expanduser("~"), "Desktop")
PARAMS_EXP = os.path.join(PARAMS_DTP, f"latest_{date.today()}")


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
        self.frm_prm = Sub(master=self)
        self.frm_prm.grid(row=1, column=0, padx=10, pady=(5,5), sticky="nesw", columnspan=1)
        self.btn_cmc = customtkinter.CTkButton(master=self, text="Commence", command=self.app_exp)
        self.btn_cmc.grid(row=2, column=0, padx=10, pady=(5,10), sticky="nesw", columnspan=1)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on call ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def app_exp(self):
        """
        Function: commence the export of collected user inputs.
        """


class Exp(customtkinter.CTkFrame):
    """
    Class: ctk frame for specifying experiment folder.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        # -------------------------------------- GUI setting --------------------------------------
        # create file path entry and label
        self.lbl_pth = customtkinter.CTkLabel(
            master = self,
            width = 50,
            height = 28,
            text = "Experiment Folder:"
        )
        self.lbl_pth.grid(row=0, column=0, padx=(10,0), pady=5, columnspan=1)
        self.ent_pth = customtkinter.CTkEntry(
            master = self,
            width = 575,
            height = 28,
            textvariable = tk.StringVar(master=self, value=PARAMS_EXP)
        )
        self.ent_pth.grid(row=0, column=1, padx=(0,5), pady=5, columnspan=1)
        self.btn_aof = customtkinter.CTkButton(
            master = self,
            width = 28,
            height = 28,
            text = "...",
            command = self.app_aof
        )
        self.btn_aof.grid(row=0, column=2, padx=(0,10), pady=5, columnspan=1)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on call ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def app_aof(self):
        """
        Function: set ent_pth to filedialog.askdirectory output.
        """
        file_path = open_file_dialog(
            init_title = "Select experiment folder",
            init_dir = PARAMS_DTP,
            init_types = False
        )
        if file_path != "":
            self.ent_pth.configure(textvariable=tk.StringVar(master=self, value=file_path))


class Sub(customtkinter.CTkFrame):
    """
    Class: ctk frame for adding individual instrument commands.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        # -------------------------------------- GUI setting --------------------------------------
        # define configuration parameters for submasking
        frames_config = [
            {"width": 144, "label": "  Number of Ports", "textvar": 20, "padx": (10,0)},
            {"width": 144, "label": "  Scan Size (um)", "textvar": 300, "padx": (10,0)},
            {"width": 144, "label": "  Concatenations", "textvar": 3, "padx": (10,0)},
            {"width": 144, "label": "  Subdivision Factor", "textvar": 3, "padx": (10,0)},
            {"width": 144, "label": "  Number of Batches", "textvar": 1, "padx": (10,10)},
        ]
        frames_list = []
        # create frames to control submasking parameters
        for i, config in enumerate(frames_config):
            entry = Entry(
                master = self,
                width = config["width"],
                label = config["label"],
                textvar = config["textvar"],
                fg_color = "transparent"
            )
            entry.grid(row=0, column=i, padx=config["padx"], pady=(5,10))
            frames_list.append(entry)


class Entry(customtkinter.CTkFrame):
    """
    Class: ctk frame for one parameter (label + entry).
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, master, label, width = None, textvar = None, placeholder = None, **kwargs):
        super().__init__(master, **kwargs)
        # ------------------------------ initialize frame GUI layout ------------------------------
        self.label = customtkinter.CTkLabel(
            master = self,
            text = label,
            anchor = "w"
        )
        self.label.grid(row=0, column=0, padx=0, pady=0)
        if width is not None:
            self.label.configure(width=width)
        self.entry = customtkinter.CTkEntry(
            master = self
        )
        if width is not None:
            self.entry.configure(width=width)
        if textvar is not None:
            self.entry.configure(textvariable=tk.StringVar(master=self, value=textvar))
        elif placeholder is not None:
            self.entry.configure(placeholder_text=placeholder)
        self.entry.grid(row=1, column=0, padx=0, pady=0)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on call ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def get_entry(self):
        """
        Function: return input in the entry as string.
        """
        return self.entry.get()


# ===================================== independent functions =====================================

def generate_digit_sequences(num_fov, num_concat=3, num_port=20):
    """
    ### Generate unique bit sequences for a given number of images.

    `num_fov` : Number of sequences to return.
    `num_concat` : Number of ones in each sequence.
    `num_port` : Length of each sequence.
    """
    # Calculate total possible combinations
    max_combinations = math.comb(num_port, num_concat)
    if num_fov > max_combinations:
        raise IndexError(f"`num_fov` exceeded max {max_combinations} for {num_concat} concat(s).")
    # generate combinations of positions where 1s should be placed
    # combinations() generates them in lexicographic order
    one_positions = combinations(range(num_port), num_concat)
    sequences = []
    for positions in one_positions:
        if len(sequences) >= num_fov:
            break
        # Create sequence with 0s
        sequence = [0] * num_port
        # Set 1s at specified positions
        for pos in positions:
            sequence[pos] = 1
        sequences.append(sequence)
    return sequences


def read_xycoordinates(csv_file):
    """
    Function: read row 1 and 2 as x and y coordinates (ignore row 0)
    """
    # read .csv, save xy coordinates in list, and print
    csv = pd.read_csv(csv_file).values.tolist()
    coords = []
    for row in csv:
        # if needed, invert x (row[1]) or y (row[2]) axis here
        coords.append([row[1], row[2]])
    # create regions in matplotlib based on the coordinates
    return coords


def count_non_white_pixel(img: Image.Image) -> int:
    """
    Function: count the number of non-white pixels in an image
    """
    white_index = img.getpalette()[0:3]  # RGB for index 0
    for i in range(256):
        if img.getpalette()[i*3:i*3+3] == [255, 255, 255]:
            white_index = i
            break
    else:
        white_index = None  # No white found in palette
    pixels = img.getdata()
    if white_index is None:
        return len(pixels)
    return sum(1 for p in pixels if p != white_index)


def global_mask_stitching(
        mask_folder,
        multichannel_coordinate,
        output_file,
        mask_affix = '.png',
        laser_cleave_size_um = 300,
        multichannel_size_um = 366,
        pixel_per_micron = 2,
        submask_division = 10,
        submask_minpixel = 100
    ):
    """
    Function: create global mask from mask folder, return coordinates for cleave areas and submasks
    """
    # get PNG files sorted by name
    image_files = sorted([f for f in os.listdir(mask_folder) if f.lower().endswith(mask_affix)])
    # get multichannel coordinates
    coordinates = read_xycoordinates(multichannel_coordinate)
    # check if number of multichannel images matches with coordinates
    if len(image_files) != len(coordinates):
        # error: mismatch between number of images and coordinate entries.
        return (
            False,  # global mask construction failed
            laser_cleave_size_um,
            [],
            [],
            [],
            []
        )
    # find min and max xy coordinates in the original um data
    min_x_um = min(x for x, y in coordinates)
    max_x_um = max(x for x, y in coordinates)
    min_y_um = min(y for x, y in coordinates)
    max_y_um = max(y for x, y in coordinates)
    range_x_um = abs(max_x_um - min_x_um)
    range_y_um = abs(max_y_um - min_y_um)
    # find the dimension of 300 um laser cleave coverage grid
    dim_x_cleaves = math.ceil((range_x_um + multichannel_size_um) / laser_cleave_size_um)
    dim_y_cleaves = math.ceil((range_y_um + multichannel_size_um) / laser_cleave_size_um)
    global_mask_width = dim_x_cleaves * laser_cleave_size_um * pixel_per_micron
    global_mask_height = dim_y_cleaves * laser_cleave_size_um * pixel_per_micron
    output_image = Image.new(
        'P',
        (global_mask_width, global_mask_height),
        color = (255,255,255)
    )
    # calculate the starting xy coordinates (top-left center)
    starting_x_px = (global_mask_width - (range_x_um + multichannel_size_um)*pixel_per_micron) / 2
    starting_y_px = (global_mask_height - (range_y_um + multichannel_size_um)*pixel_per_micron) / 2
    starting_x_um = (min_x_um
                      - (starting_x_px / pixel_per_micron)  # adjust for global mask's larger size
                      - (multichannel_size_um - laser_cleave_size_um)/2 # adjust for cleavage size
                    )
    starting_y_um = (max_y_um
                      + (starting_y_px / pixel_per_micron)  # adjust for global mask's larger size
                      + (multichannel_size_um - laser_cleave_size_um)/2 # adjust for cleavage size
                    )
    # stitch global mask using multichannel coordinates
    for i, xy_pair in enumerate(coordinates):
        x_px = int(starting_x_px + (xy_pair[0] - min_x_um) * pixel_per_micron)
        y_px = int(starting_y_px + (max_y_um - xy_pair[1]) * pixel_per_micron)
        img_path = os.path.join(mask_folder, image_files[i])
        img = Image.open(img_path).convert('P')
        pyplot_create_region(
            x = xy_pair[0],
            y = xy_pair[1],
            w = multichannel_size_um,
            h = multichannel_size_um,
            c = 'w',
            e = 'w',
            j = img_path,
            a = 0.5,
            g = 0.25,
            r = 180
        )
        img = img.transpose(method=Image.Transpose.FLIP_LEFT_RIGHT)
        img = img.transpose(method=Image.Transpose.FLIP_TOP_BOTTOM)
        output_image.paste(img, (x_px, y_px))
    # calculate submask dimension in um and px
    submask_dimension_um = int(laser_cleave_size_um / submask_division)
    submask_dimension_px = int(submask_dimension_um * pixel_per_micron)
    # calculate xy coordinates for the top-left tip (um)
    topleft_x_um = starting_x_um - laser_cleave_size_um/2
    topleft_y_um = starting_y_um + laser_cleave_size_um/2
    # map out center coordinates for cleavage areas (um)
    # also map out submask coordinates (px for top-left, um for center)
    cleave_center_coord_um = []
    cleave_center_coord_px = []
    submask_coordinates_px = []
    submask_coordinates_um = []
    current_x = starting_x_um
    current_y = starting_y_um
    current_i = 0
    for row in range(dim_y_cleaves):
        for col in range(dim_x_cleaves):
            # append xy cleave coordinates in um
            cleave_center_coord_um.append([current_x, current_y])
            pyplot_create_region(
                current_x,
                current_y,
                laser_cleave_size_um,
                laser_cleave_size_um,
                c = 'r',
                e = 'r',
                i = current_i,
                a = 0.5,
                g = 0.75
            )
            # produce xy coordinates for non-empty submasks (px)
            xy_displacement = ((submask_dimension_px*(submask_division-1))/2)/pixel_per_micron
            f0_submask_x_um = current_x - xy_displacement
            f0_submask_y_um = current_y + xy_displacement
            f0_submask_x_px = ((current_x-laser_cleave_size_um/2) - topleft_x_um)*pixel_per_micron
            f0_submask_y_px = (topleft_y_um - (current_y+laser_cleave_size_um/2))*pixel_per_micron
            cleave_center_coord_px.append([f0_submask_x_px,
                                           f0_submask_y_px,
                                           f0_submask_x_px + laser_cleave_size_um*pixel_per_micron,
                                           f0_submask_y_px + laser_cleave_size_um*pixel_per_micron
                                          ])
            for i in range(submask_division):
                for j in range(submask_division):
                    # check if the submask area is empty (below minimum pixel count threshold)
                    location_x_um = int(f0_submask_x_um + j*submask_dimension_um)
                    location_y_um = int(f0_submask_y_um - i*submask_dimension_um)
                    location_x_px = int(f0_submask_x_px + j*submask_dimension_px)
                    location_y_px = int(f0_submask_y_px + i*submask_dimension_px)
                    submask_locus = [location_x_px,
                                     location_y_px,
                                     location_x_px + submask_dimension_px,
                                     location_y_px + submask_dimension_px]
                    submask_section = output_image.crop(submask_locus)
                    if count_non_white_pixel(submask_section) > submask_minpixel:
                        submask_coordinates_um.append([location_x_um, location_y_um])
                        submask_coordinates_px.append(submask_locus)
                        pyplot_create_region(
                            location_x_um,
                            location_y_um,
                            submask_dimension_um,
                            submask_dimension_um,
                            c = 'r',
                            e = 'r',
                            a = 0.1
                        )
            # update coordinates and index
            current_i += 1
            if col != (dim_x_cleaves - 1):
                # move the coordinates based on which row it sits
                if row % 2 == 0:
                    # if it's an even number row, move to the right
                    current_x += laser_cleave_size_um
                else:
                    # if it's an odd number row, move to the left
                    current_x -= laser_cleave_size_um
            else:
                # then instead of moving the x coordinate, move the y coordinate
                # this will move the current xy coordinates to the next row
                current_y -= laser_cleave_size_um
    # save the constructed global laser image, return
    output_image.save(output_file)
    return (
        True,   # global mask construction successful
        laser_cleave_size_um,
        cleave_center_coord_um,
        cleave_center_coord_px,
        submask_coordinates_um,
        submask_coordinates_px
    )


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
