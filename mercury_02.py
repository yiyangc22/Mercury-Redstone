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

WINDOW_TXT = "Mercury II - Laser Scheme Constructor"
WINDOW_RES = "800x190"
PARAMS_CFG = [
                {"width": 144, "label": "  Number of Ports", "textvar": 20, "padx": (10,0)},
                {"width": 144, "label": "  Scan Size (um)", "textvar": 300, "padx": (10,0)},
                {"width": 144, "label": "  Concatenations", "textvar": 5, "padx": (10,0)},
                {"width": 144, "label": "  Subdivision Factor", "textvar": 3, "padx": (10,0)},
                {"width": 144, "label": "  Pixel Count Threshold", "textvar": 100, "padx": (10,10)},
             ]
PARAMS_TRL = "_MC_F001_Z001.png"

PARAMS_DTP = os.path.join(os.path.expanduser("~"), "Desktop")
PARAMS_EXP = os.path.join(PARAMS_DTP, f"latest_{date.today()}")
PARAMS_MCI = "image_multichannel"
PARAMS_MSK = "image_mask"
PARAMS_LSR = "image_laser"
PARAMS_MAP = "image_cleave_map"
PARAMS_PLN = "coord_planned.csv"
PARAMS_CRD = "coord_recorded.csv"
PARAMS_GLB = "image_mask_global.png"
PARAMS_SCT = "coord_scan_center.csv"
PARAMS_BIT = "config_bit_scheme.csv"
PARAMS_TMP = "image_mask_tmp.png"


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
        # ----------------------------------- parameter setting -----------------------------------
        self.pth_fld = PARAMS_EXP
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on call ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def app_exp(self):
        """
        Function: commence the export of collected user inputs.
        """
        # collect parameters for global/submask constuction
        try:
            # read inputs from entry frames
            num_ports = int(self.frm_prm.frames_list[0].get_entry())
            scan_size = int(self.frm_prm.frames_list[1].get_entry())
            num_conct = int(self.frm_prm.frames_list[2].get_entry())
            num_subdv = int(self.frm_prm.frames_list[3].get_entry())
            num_count = int(self.frm_prm.frames_list[4].get_entry())
        except (ValueError, TypeError, RuntimeError) as e:
            print(f"Warning: {e}, check parameter input format.")
        # construct global mask
        try:
            # read inputs from entry frames
            self.pth_fld = self.frm_ctl.ent_pth.get()
            exp_coord = os.path.join(self.pth_fld, PARAMS_PLN)
            exp_gmask = os.path.join(self.pth_fld, PARAMS_GLB)
            exp_rcrdz = os.path.join(self.pth_fld, PARAMS_CRD)
            # process parameters, save results
            (successful,
            _cleave_size,
            cleave_center_coord_um,
            cleave_center_coord_px,
            submask_coordinates_um,
            submask_coordinates_px
            ) = global_mask_stitching(
                mask_folder = os.path.join(self.pth_fld, PARAMS_MSK),
                multichannel_coordinate = exp_coord,
                output_file = exp_gmask,
                mask_affix = PARAMS_TRL,
                laser_cleave_size_um = scan_size,
                submask_division = num_subdv,
                submask_minpixel = num_count
            )
            if not successful:
                print("Error: global mask stitching failed.")
                return
        except (ValueError, TypeError, RuntimeError) as e:
            print(f"Warning: {e}, check file path and mask/coordinate indexing.")
            return
        # save a blank cleave mask for future uses
        blank_mask = Image.new('P', [1024,1024], color = (255,255,255))
        blank_mask.save(os.path.join(self.pth_fld, PARAMS_TMP), format='PNG')
        # save generated cleave center coordinates
        cleave_centers = []
        plan_xy_value = read_xycoordinates(exp_coord)
        record_z_value = read_zcoordinates(exp_rcrdz)
        print(len(record_z_value))
        for i, coord_pair in enumerate(cleave_center_coord_um):
            temp = coord_pair
            nearest_z = record_z_value[find_closest_coordinate(plan_xy_value, coord_pair)]
            temp.append(nearest_z)
            temp.extend(cleave_center_coord_px[i])
            cleave_centers.append(temp)
        dataframe = pd.DataFrame(cleave_centers, columns=['x','y','z','w','n','e','s'])
        dataframe.to_csv(os.path.join(self.pth_fld, PARAMS_SCT), index=True)
        # generate bit scheme for all subregions
        bit_scheme, max_index = generate_digit_sequences(
            len(submask_coordinates_um),
            num_conct,
            num_ports
        )
        # convert bit scheme into port sequences
        port_config = []
        for sequence in bit_scheme:
            temp = []
            for i, bit in enumerate(sequence):
                if bit == 1:
                    temp.append(i)
            port_config.append(temp)
        # save generated submask laser/port scheme
        fluidic_scheme = []
        for i, coord_pair in enumerate(submask_coordinates_um):
            temp = coord_pair
            temp.extend(submask_coordinates_px[i][:])
            temp.append(port_config[i])
            temp.append(bit_scheme[i])
            fluidic_scheme.append(temp)
        dataframe = pd.DataFrame(fluidic_scheme, columns=['x','y','w','n','e','s','index','bit'])
        dataframe.to_csv(os.path.join(self.pth_fld, PARAMS_BIT), index=True)
        # generate a new cleave map image
        global_mask = Image.open(exp_gmask)
        global_mask_w, global_mask_h = global_mask.size
        tmp_map = Image.new('P',
                            (global_mask_w, global_mask_h),
                            color = (255,255,255))
        # generate cleavage maps, save cleave image
        for i in range(max_index):
            # clear previous cleave mask markings
            ImageDraw.Draw(tmp_map).rectangle(
                (0, 0, global_mask_w, global_mask_h),
                fill = (255,255,255)
            )
            # append images for matching submasks
            for k, indexes in enumerate(fluidic_scheme):
                if indexes[7][i] == 1:
                    this_region = global_mask.crop(submask_coordinates_px[k])
                    tmp_map.paste(this_region, submask_coordinates_px[k])
            # save cleave map if the port != -1
            tmp_map.save(os.path.join(self.pth_fld, PARAMS_MAP, ('Round ' + str(i) + '.png')),
                         format = 'PNG')
        # preview saved submask areas in matplotlib
        plt.gca().set_aspect('equal')
        plt.gcf().set_figheight(10)
        plt.gcf().set_figwidth(10)
        plt.show()
        # quit customtkinter mainloop
        self.quit()
    # ---------------------------------------------------------------------------------------------
    def on_closing(self):
        """
        Function: enforce quit manually before closing.
        """
        self.quit()


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
        frames_config = PARAMS_CFG
        self.frames_list = []
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
            self.frames_list.append(entry)


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
    ### Function: generate unique bit sequences for a given number of images.

    `num_fov` : Number of sequences to return.
    `num_concat` : Number of ones in each sequence.
    `num_port` : Length of each sequence.
    """
    # # calculate total possible combinations
    # max_combinations = math.comb(num_port, num_concat)
    # if num_fov > max_combinations:
    #     print(f"`num_fov` exceeded max {max_combinations} for {num_concat} concat(s).")
    #     return []
    # calculate minimum columns needed
    columns = num_concat
    while math.comb(columns, num_concat) < num_fov:
        columns += 1
    if columns > num_port:
        print(f"`num_fov` exceeded max allowed combinations for {num_concat} concat(s).")
        return ([], columns)
    # generate combinations of positions where 1s should be placed
    # combinations() generates them in lexicographic order
    one_positions = combinations(range(columns), num_concat)
    sequences = []
    for positions in one_positions:
        if len(sequences) >= num_fov:
            break
        # Create sequence with 0s
        sequence = [0] * columns
        # Set 1s at specified positions
        for pos in positions:
            sequence[pos] = 1
        sequences.append(sequence)
    return (sequences, columns)


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


def read_zcoordinates(csv_file):
    """
    Function: read row 3 as z coordinates (ignore row 0, 1, 2)
    """
    # read .csv, save xy coordinates in list, and print
    csv = pd.read_csv(csv_file).values.tolist()
    coords = []
    for row in csv:
        # if needed, invert x (row[1]) or y (row[2]) axis here
        coords.append(row[3])
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
        pixel_per_micron = 1,
        submask_division = 10,
        submask_minpixel = 100
    ):
    """
    Function: create global mask from mask folder, return coordinates for cleave areas and submasks
    """
    # get PNG files sorted by name
    image_files = sorted([f for f in os.listdir(mask_folder) if f.endswith(mask_affix)])
    print("Number of images: ", len(image_files))
    # get multichannel coordinates
    coordinates = read_xycoordinates(multichannel_coordinate)
    print("Number of coordinate pairs: ", len(coordinates))
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
    output_image.save(output_file, format='PNG')
    return (
        True,   # global mask construction successful
        laser_cleave_size_um,
        cleave_center_coord_um,
        cleave_center_coord_px,
        submask_coordinates_um,
        submask_coordinates_px
    )


def find_closest_coordinate(coordinates, point):
    """
    Function: ind the index of the coordinate pair that is closest to the given point.
    
    Args:
        coordinates: List of coordinate pairs [[x1, y1], [x2, y2], ...]
        point: Target point [x, y]
    
    Returns:
        int: Index of the closest coordinate pair
    """
    target_x, target_y = point
    min_distance = float('inf')
    closest_index = 0
    # loop through all possible xy pairs
    for i, coord in enumerate(coordinates):
        x = coord[0]
        y = coord[1]
        # calculate Euclidean distance
        distance = ((x - target_x) ** 2 + (y - target_y) ** 2) ** 0.5
        # keep the index of the closest coordinate pair
        if distance == 0:
            return i
        elif distance < min_distance:
            min_distance = distance
            closest_index = i
    return closest_index


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
        app.protocol("WM_DELETE_WINDOW", app.on_closing)
        app.mainloop()
    except AttributeError:
        return None
