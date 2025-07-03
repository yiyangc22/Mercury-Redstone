"""
Mercury 01: image scheme constructor, project version 1.22B (with python 3.9).
"""

import os
import math
import tkinter
from tkinter import filedialog

import customtkinter
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image

WINDOW_TXT = "Mercury I - Image Scheme Constructor"
WINDOW_RES = "807x237"
PARAMS_DTP = os.path.join(os.path.expanduser("~"), "Desktop")
PARAMS_FLD = os.path.join(PARAMS_DTP, "Latest")
PARAMS_TAB = ["Global Tissue", "Square Subgroup"]
PARAMS_CRN = 4
PARAMS_RES = 366
PARAMS_MCI = "Multichannel Images"
PARAMS_MSK = "Mask Images"
PARAMS_MAP = "Cleave Maps"
PARAMS_PLN = "Imaging Coordinates - Planned.csv"
PARAMS_CRD = "Imaging Coordinates - Recorded.csv"


# ===================================== customtkinter classes =====================================

class Moa:
    """
    Class: mother of all classes, parent and pass inputs from customtkinter.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self):
        super().__init__()
        self.rtn = ([], '', 0.0)


class App(customtkinter.CTk, Moa):
    """
    Class: main application window and customtkinter main loop.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, sample_x = None, sample_y = None, sample_z = None):
        super().__init__()
        # ---------------------------------- application setting ----------------------------------
        self.title(WINDOW_TXT)
        self.geometry(WINDOW_RES)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        # save the sample z value
        self.sample_x = sample_x
        self.sample_y = sample_y
        self.sample_z = sample_z
        # -------------------------------------- GUI setting --------------------------------------
        # create tabviews for global tissue imaging and subgroup imaging
        self.tab_ent = customtkinter.CTkTabview(master=self)
        self.tab_ent.add(PARAMS_TAB[0])
        self.tab_ent.add(PARAMS_TAB[1])
        self.tab_ent.grid(row=0, column=0, padx=10, pady=(0,5), sticky="ew", columnspan=3)
        # configure the tabview for global tissue imaging
        # min x
        self.inp_minx = Entry(
            master = self.tab_ent.tab(PARAMS_TAB[0]),
            width = 105,
            label = "  Min X - Left",
            placeholder = "(Required)"
        )
        self.inp_minx.grid(row=0, column=1, padx=(0,5), pady=0)
        # max x
        self.inp_maxx = Entry(
            master = self.tab_ent.tab(PARAMS_TAB[0]),
            width = 105,
            label = "  Max X - Right",
            placeholder = "(Required)"
        )
        self.inp_maxx.grid(row=0, column=2, padx=(0,5), pady=0)
        # min y
        self.inp_miny = Entry(
            master = self.tab_ent.tab(PARAMS_TAB[0]),
            width = 105,
            label = "  Min Y - Bottom",
            placeholder = "(Required)"
        )
        self.inp_miny.grid(row=0, column=3, padx=(0,5), pady=0)
        # max y
        self.inp_maxy = Entry(
            master = self.tab_ent.tab(PARAMS_TAB[0]),
            width = 105,
            label = "  Max Y - Top",
            placeholder = "(Required)"
        )
        self.inp_maxy.grid(row=0, column=4, padx=(0,5), pady=0)
        # corner radii
        self.inp_crn = Entry(
            master = self.tab_ent.tab(PARAMS_TAB[0]),
            width = 105,
            label = "  Corner Radii",
            textvar = PARAMS_CRN
        )
        self.inp_crn.grid(row=0, column=5, padx=(0,5), pady=0)
        # starting z
        self.inp_rz0 = Entry(
            master = self.tab_ent.tab(PARAMS_TAB[0]),
            width = 105,
            label = "  Starting Z",
            textvar = self.sample_z,
            placeholder = "(Required)"
        )
        self.inp_rz0.grid(row=0, column=6, padx=(0,5), pady=0)
        # scan resolution
        self.inp_rs0 = Entry(
            master = self.tab_ent.tab(PARAMS_TAB[0]),
            width = 105,
            label = "  Resolution",
            textvar = PARAMS_RES
        )
        self.inp_rs0.grid(row=0, column=7, padx=(0,5), pady=0)
        # configure the tabview for square subgroup imaging
        # center x
        self.inp_ctrx = Entry(
            master = self.tab_ent.tab(PARAMS_TAB[1]),
            width = 215,
            label = "  Center X",
            textvar = self.sample_x,
            placeholder = "(Required)"
        )
        self.inp_ctrx.grid(row=0, column=1, padx=(0,6), pady=0)
        # center y
        self.inp_ctry = Entry(
            master = self.tab_ent.tab(PARAMS_TAB[1]),
            width = 215,
            label = "  Center Y",
            textvar = self.sample_y,
            placeholder = "(Required)"
        )
        self.inp_ctry.grid(row=0, column=2, padx=(0,6), pady=0)
        # subgroup dimension
        self.inp_dim = Entry(
            master = self.tab_ent.tab(PARAMS_TAB[1]),
            width = 105,
            label = "  Dimension",
            placeholder = "(Required)"
        )
        self.inp_dim.grid(row=0, column=5, padx=(0,5), pady=0)
        # starting z
        self.inp_rz1 = Entry(
            master = self.tab_ent.tab(PARAMS_TAB[1]),
            width = 105,
            label = "  Starting Z",
            textvar = self.sample_z,
            placeholder = "(Required)"
        )
        self.inp_rz1.grid(row=0, column=6, padx=(0,5), pady=0)
        # scan resolution
        self.inp_rs1 = Entry(
            master = self.tab_ent.tab(PARAMS_TAB[1]),
            width = 105,
            label = "  Resolution",
            textvar = PARAMS_RES
        )
        self.inp_rs1.grid(row=0, column=7, padx=(0,5), pady=0)
        # create file path entry and label
        self.lbl_pth = customtkinter.CTkLabel(
            master = self,
            width = 50,
            height = 28,
            text = "Experiment Save Path:"
        )
        self.lbl_pth.grid(row=1, column=0, padx=(10,0), pady=5, columnspan=1)
        self.ent_pth = customtkinter.CTkEntry(
            master = self,
            width = 575,
            height = 28,
            textvariable = tkinter.StringVar(master=self, value=PARAMS_FLD)
        )
        self.ent_pth.grid(row=1, column=1, padx=(0,5), pady=5, columnspan=1)
        self.btn_aof = customtkinter.CTkButton(
            master = self,
            width = 28,
            height = 28,
            text = "...",
            command = self.app_aof
        )
        self.btn_aof.grid(row=1, column=2, padx=(0,10), pady=5, columnspan=1)
        # configure preview and commence buttons
        self.btn_prv = customtkinter.CTkButton(
            master = self,
            text = "Preview Scheme",
            command = self.app_prv,
            fg_color = "transparent",
            border_width = 1,
            hover_color = "gray23"
        )
        self.btn_prv.grid(row=2, column=0, padx=10, pady=5, sticky="ew", columnspan=3)
        self.btn_cmc = customtkinter.CTkButton(master=self, text="Commence", command=self.app_exp)
        self.btn_cmc.grid(row=3, column=0, padx=10, pady=(5,10), sticky="ew", columnspan=3)
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
        self.ent_pth.configure(textvariable=tkinter.StringVar(master=self, value=file_path))
    # ---------------------------------------------------------------------------------------------
    def app_prv(self, save: bool = False):
        """
        Function: get a preview of the scan scheme with pyplot.
        """
        # check which tab is active and read from it
        try:
            if self.tab_ent.get() == PARAMS_TAB[0]:
                return scheme_export_packed(
                    scheme_create_global(
                        float(self.inp_minx.get_entry()),
                        float(self.inp_maxx.get_entry()),
                        float(self.inp_miny.get_entry()),
                        float(self.inp_maxy.get_entry()),
                        int(self.inp_crn.get_entry()),
                        float(self.inp_rs0.get_entry())
                    ),
                    self.ent_pth.get(),
                    float(self.inp_rz0.get_entry()),
                    save,
                    float(self.inp_rs0.get_entry())
                )
            if self.tab_ent.get() == PARAMS_TAB[1]:
                return scheme_export_packed(
                    scheme_create_subgrp(
                        float(self.inp_ctrx.get_entry()),
                        float(self.inp_ctry.get_entry()),
                        int(self.inp_dim.get_entry()),
                        float(self.inp_rs1.get_entry())
                    ),
                    self.ent_pth.get(),
                    float(self.inp_rz1.get_entry()),
                    save,
                    float(self.inp_rs1.get_entry())
                )
        except ValueError:
            print("Warning: parameter format error, check parameter inputs.")
    # ---------------------------------------------------------------------------------------------
    def app_exp(self):
        """
        Function: commence the export of collected user inputs.
        """
        # save return values
        self.rtn = self.app_prv(save=True)
        # save planned xy coordinates
        planned_coordinates, multichannel_image, _ = self.rtn
        file_path = os.path.join(os.path.dirname(multichannel_image), PARAMS_PLN)
        column_names = ["x", "y"]
        df = pd.DataFrame(planned_coordinates, columns=column_names)
        df.to_csv(file_path, index=True)
        # quit customtkinter mainloop
        self.quit()


class Entry(customtkinter.CTkFrame):
    """
    Class: ctk frame for one parameter (label + entry).
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, master, width, label, textvar = None, placeholder = None, **kwargs):
        super().__init__(master, **kwargs)
        # ------------------------------ initialize frame GUI layout ------------------------------
        self.label = customtkinter.CTkLabel(
            master = self,
            width = width,
            text = label,
            anchor = "w"
        )
        self.label.grid(row=0, column=0, padx=0, pady=0)
        self.entry = customtkinter.CTkEntry(
            master = self,
            width = width
        )
        if textvar is not None:
            self.entry.configure(textvariable=tkinter.StringVar(master=self, value=textvar))
        elif placeholder is not None:
            self.entry.configure(placeholder_text=placeholder)
        self.entry.grid(row=1, column=0, padx=0, pady=0)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on call ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def get_entry(self):
        """
        Function: return input in the entry as string.
        """
        return self.entry.get()


# ====================================== scheme construction ======================================

def scheme_export_packed(
        l: list,                 # xy coordinates for the imaging fields
        p: str,                  # file save path for the exported image
        z: float,                # recommended z value from user entries
        s: bool,                 # preview if false, save & exit if true
        d: float                 # user scan size (as recorded in entry)
):
    """
    ### Return a 2d list of xy pairs, an image save path string, and a recommended z value.

    `l` : xy coordinates for the imaging fields.
    `p` : file save path for the exported image.
    `z` : recommended z value from user entries.
    `s` : preview if false, save & exit if true.
    `d` : user scan size (as recorded in entry).
    """
    # check if the given path already exists, change the save path if necessary
    duplicated = False
    root = p
    if os.path.isdir(p):
        count = 1
        p += f" ({count})"
        duplicated = True
        while os.path.isdir(p):
            count += 1
            p = root + f" ({count})"
    # for save & exit
    if s:
        # save relevant files/folders
        try:
            # make directory for experiment folder and multichannel image folder
            os.makedirs(os.path.join(p, PARAMS_MCI))
            # make directory for laser mask folder and laser image folder
            os.makedirs(os.path.join(p, PARAMS_MSK))
            # make directory for laser cleave maps and cleave maps folder
            os.makedirs(os.path.join(p, PARAMS_MAP))
            # create file for storing recorded xyz values
            df = pd.DataFrame({'x':[], 'y':[], 'z':[]})
            df.to_csv(os.path.join(p, PARAMS_CRD))
        except FileExistsError:
            print(f"Warning: overwriting file(s) at {p}.")
    # for previewing
    else:
        # create textbox to display FOV parameters
        txt = f"Number of images: {len(l)}\n"
        txt += f"Projected scan size: {PARAMS_RES}\n"
        txt += f"User scan size: {d}\n"
        txt += f"Experiment folder: {p}"
        if duplicated:
            txt += "\n**Warning: folder name changed due to name duplication**"
        plt.text(
            x = 1.05,
            y = 1,
            s = txt,
            transform = plt.gca().transAxes,
            fontsize = 10,
            verticalalignment='top',
            bbox = dict(facecolor='none', alpha=0.15)
        )
        # show pyplot preview in a separate window
        plt.gca().set_aspect('equal')
        plt.gcf().set_figwidth(15)
        plt.gcf().set_figheight(7.5)
        plt.tight_layout()
        plt.show()
    # return xy list and image save path
    return (l, os.path.join(p, PARAMS_MCI), z)


def scheme_create_global(
        min_x: float,
        max_x: float,
        min_y: float,
        max_y: float,
        scan_crn: int,
        scan_res: float,
):
    """
    ### Return a tuple of xy coordinates and the autofocus scheme, passing a plot preview.

    `min_x` : minimum x value (left).
    `max_x` : maximum x value (right).
    `min_y` : minimum y value (down).
    `max_y` : maximum y value (up).
    `scan_crn` : corner radius of the scan scheme.
    `scan_res` : scan resolution of each image (IU or um).
    """
    # make sure scan resolution and corner radii are constant and always positive
    res = abs(scan_res)
    crn = abs(scan_crn)
    # find center coordinates, tissue ranges, and scan dimensions
    center_x = round((max_x + min_x) / 2)   # must be int
    center_y = round((max_y + min_y) / 2)   # must be int
    range_x = abs(max_x - min_x)            # must be positive
    range_y = abs(max_y - min_y)            # must be positive
    dim_x = math.ceil(range_x / res)        # must be int
    dim_y = math.ceil(range_y / res)        # must be int
    # initialize corner mapping and return variable
    crn_map = scheme_create_crnmap(dim_y, dim_x, crn)
    # initialize local variables
    current_x = 0
    current_y = 0
    current_i = 0
    rtn = []
    # find start coordinates (on the top-left corner) of the tissue
    if dim_x % 2 != 0:
        current_x = center_x - math.floor(dim_x / 2) * res
    else:
        current_x = center_x - (math.floor(dim_x / 2) - 0.5) * res
    if dim_y % 2 != 0:
        current_y = center_y + math.floor(dim_y / 2) * res
    else:
        current_y = center_y + (math.floor(dim_y / 2) - 0.5) * res
    # loop through all imaging positions (in an S-shape order)
    # append xy coordinates, pfs, and store a preview into pyplot
    for row in range(dim_y):
        for col in range(dim_x):
            # if the image is a center image (stored as 0 in MAP)
            if crn_map[row][col] == 0:
                # first append the image's coordinates
                rtn.append([current_x, current_y])
                # store a preview area in pyplot
                pyplot_create_region(
                    current_x,
                    current_y,
                    PARAMS_RES,
                    PARAMS_RES,
                    c = 'b',
                    e = 'b',
                    i = current_i
                )
                # increment the number of images taken
                current_i += 1
            # move the coordinates to the next region
            if col != (dim_x - 1):
                # move the coordinates based on which row it sits
                if row % 2 == 0:
                    # if it's an even number row, move to the right
                    current_x += res
                else:
                    # if it's an odd number row, move to the left
                    current_x -= res
            else:
                # then instead of moving the x coordinate, move the y coordinate
                # this will move the current xy coordinates to the next row
                current_y -= res
    # return compiled xy coordinates
    return rtn


def scheme_create_subgrp(
        cursor_x: float,        # cursor x coordinate for this subgroup             float / int
        cursor_y: float,        # cursor y coordinate for this subgroup             float / int
        region_n: int,          # number of FOV scans, on one side of a subgroup    int
                                # (i.e. a 4x4 subgroup should have region_n = 4)
        region_s: float,        # xy size of FOV scans in given units               float / int
):
    """
    ### Return a tuple of xy coordinates and the autofocus scheme, passing a plot preview.

    `x` : center x coordinate.
    `y` : center y coordinate.
    `n` : number of FOV scans on each side of the subgroup.
    `s` : xy size of FOV scans in given units.
    """
    # ------------------------------ initialize and adjust variables ------------------------------
    r = region_s                # distance between the centers of adjacent FOVs
    c = "down"                  # cardinal directions for the cursor to move to
    x = cursor_x                # cursor x position, initially at the center of the subgroup
    y = cursor_y                # cursor y position, initially at the center of the subgroup
    i = 0                       # index of the FOV that the cursor is currently at
    j = 0                       # number of times the append direction was changed
    k = 0                       # number of times the cursor moves before it turns
    rtn = []                    # return list
    # if region_n is even, adjust cursor xy to the center of adjacent FOV at the lower-right corner
    if (region_n % 2) == 0:
        cursor_x += (0.5 * r)
        cursor_y -= (0.5 * r)
        x += (0.5 * r)
        y -= (0.5 * r)
    # ---------------------------------------- loop starts ----------------------------------------
    # spiral counter-clockwise outward, loop until all center coordinates for all FOVs are appended
    while i < (region_n * region_n):
        # for every 2 changes in the appending direction, l += 1
        if (j % 2) == 0:
            k += 1
        # turn the appending direction counter-clockwise
        # switch case is not compatable with python v3.9
        if c == "left":
            c = "up"
        elif c == "up":
            c = "right"
        elif c == "right":
            c = "down"
        elif c == "down":
            c = "left"
        # move the cursor as it appends its location for l times
        for _ in range(0, k):
            # increment the number of FOVs appended
            i += 1
            # append the current cursor coordinates as a 1D list
            rtn.append([x, y])
            # save a preview of the current FOV area into pyplot
            pyplot_create_region(x, y, PARAMS_RES, PARAMS_RES, c="g", e="g", i=i)
            # move to the next FOV depending on cursor direction
            if c == "left":     # move one FOV left
                x -= r
            elif c == "up":     # move one FOV up
                y += r
            elif c == "right":  # move one FOV right
                x += r
            elif c == "down":   # move one FOV down
                y -= r
        # increment the number of turns
        j += 1
    # return rtn once the loop ends
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
        a = 1,          # alpha value of all graphic elements       float / int
        g = 1,          # alpha value of all glyphic elements       float / int
        b = False,      # flip image on W-E direction if True       bool
        d = False,      # flip image on N-S direction if True       bool
        r = 0,          # counter-clockwise rotation of image       int
        t = 0,          # counter-clockwise rotation of texts       int
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
    `a` : alpha value of all graphic elements. Default = `1`.
    `g` : alpha value of all glyphic elements. Default = `1`.
    `b` : flip image on W-E direction if True. Default = `False`.
    `d` : flip image on N-S direction if True. Default = `False`.
    `r` : counter-clockwise rotation of image. Default = `0`.
    `t` : counter-clockwise rotation of texts. Default = `0`.
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
    plt.text(x, y, i, ha=f, va=v, alpha=g, rotation=t)
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
        ax.imshow(
            np.fliplr(np.flipud(img)),
            extent = (x+0.5*w, x-0.5*w, y+0.5*h, y-0.5*h),
            alpha = a
        )
        # invert the axes back as imshow will invert x and y axis
        ax.invert_xaxis()
        ax.invert_yaxis()
        # graph rectX - recty with linestyle ':'
        plt.plot(corner_x, corner_y, ':', color=e, alpha=a)
    else:
        # graph rectX - recty with linestyle '-'
        plt.plot(corner_x, corner_y, '-', color=e, alpha=a)


def scheme_create_crnmap(
        row: int,
        col: int,
        crn: int,
):
    """
    ### Return a 2d list of int values as the mapping for cornered scheme (1 = corner, 0 = center).

    `row` : number of rows in the global scan scheme.
    `col` : number of columns in the global scan scheme.
    `crn` : desired corner radius of the scan scheme.
    """
    # set up return variable
    rtn = []
    # create empty mapping
    for i in range(0, row):
        rtn.append([])
        for _ in range(0, col):
            rtn[i].append(0)
    # set corner regions to 1; center regions remain as 0s
    for i in range(row):
        if i < crn:  # upper corners
            rtn[i][: crn - i] = [1] * (crn - i)  # upper left
            rtn[i][- (crn - i):] = [1] * (crn - i)  # upper right
        if i >= row - crn:  # lower corners
            offset = i - (row - crn)
            rtn[i][: offset + 1] = [1] * (offset + 1)  # lower left
            rtn[i][- (offset + 1):] = [1] * (offset + 1)  # lower right
    # flatten the return list, return
    return rtn


def csvset_modify_concat(
        file_path,
        new_value,
        file_name = PARAMS_CRD,
        end_level = 0
):
    """
    ### Open an existing log file, concatenate a set of xyz values.

    `file_path` : .csv file name with full path.
    `new_value` : values to write into the file.
    -----------------------------------------------------------------------------------------------
    #### Optional:
    `file_name` : name of the .csv file to edit = `"${PARAMS_LOG}"`.
    `end_level` : strings to cut from file_path = `0`.
    """
    # find target .csv file first if end_level is not 0
    if end_level != 0:
        for _ in range(end_level):
            file_path = os.path.dirname(file_path)
        file_path = os.path.join(file_path, file_name)
    # write the updated dataframe back to the .csv file
    df1 = pd.read_csv(file_path)
    df2 = pd.DataFrame({
        "x": [new_value[0]],
        "y": [new_value[1]],
        "z": [new_value[2]]
    })
    # avoid concat empty dataframes (may cause empty rows)
    if df1.empty:
        df1 = df2
    else:
        df1 = pd.concat([df1, df2], ignore_index=True)
    df1.to_csv(file_path, index=False)


def open_file_dialog(
        init_title = "Select a file",
        init_dir = "/",
        init_types = (("All files", "*.*"))
    ):
    """
    Function: open a file dialog using tkinter, return selected path.

    Note: setting `init_types` to False enables askdirectory().
    """
    if init_types is not False:
        # open file dialog and get the selected file path
        file_path = filedialog.askopenfilename(
            title = init_title,
            initialdir = init_dir,
            filetypes = init_types
        )
    else:
        # open file dialog and get the selected directory path
        file_path = filedialog.askdirectory(
            title = init_title,
            initialdir = init_dir
        )
    return file_path


# ========================================= main function =========================================

def mercury_01(
        sample_x = None,
        sample_y = None,
        sample_z = None
):
    """
    Main application loop of mercury 01, return user inputs when loop ended.
    """
    # set customtkinter appearance mode and color theme
    customtkinter.set_appearance_mode("dark")
    customtkinter.set_default_color_theme("blue")
    # enter main loop and return user inputs when ended
    app = App(sample_x, sample_y, sample_z)
    app.resizable(False, False)
    app.mainloop()
    try:
        return app.rtn
    except AttributeError:
        return ([],'',0.0)
