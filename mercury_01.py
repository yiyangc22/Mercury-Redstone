"""
Mercury 01: image scheme constructor, project version 1.2 (with python 3.9).
"""

import os
import math
import tkinter
import customtkinter
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image

WINDOW_TXT = "Mercury I - Image Scheme Constructor"
WINDOW_RES = "900x600"
PARAMS_DTP = os.path.join(os.path.expanduser("~"), "Desktop")
PARAMS_FCS = ["No Autofocus", "Image Based", "Nikon PFS"]
PARAMS_RES = 300
PARAMS_RTN = "_coordinates.csv"


# ===================================== customtkinter classes =====================================

class Moa:
    """
    Class: mother of all classes, parent and pass inputs from customtkinter.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self):
        super().__init__()
        self.rtn = ["Not Changed"]


class App(customtkinter.CTk, Moa):
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
        # create the scrollable frame list
        self.frm_lst = Lst(master=self, corner_radius=5)
        self.frm_lst.grid(row=0, column=0, padx=10, pady=5, sticky="nsew", columnspan=4)
        # create file path entry and label
        self.lbl_pth = customtkinter.CTkLabel(
            master = self,
            width = 50,
            height = 28,
            text = "Image Save Path:"
        )
        self.lbl_pth.grid(row=1, column=0, padx=(10,0), pady=5, sticky="nsew", columnspan=1)
        self.ent_pth = customtkinter.CTkEntry(
            master = self,
            width = 470,
            height = 28,
            textvariable = tkinter.StringVar(master=self, value=PARAMS_DTP)
        )
        self.ent_pth.grid(row=1, column=1, padx=(0,10), pady=5, sticky="ew", columnspan=1)
        # create entry for scan resolution
        self.lbl_res = customtkinter.CTkLabel(
            master = self,
            width = 0,
            height = 28,
            text = "Scan Resolution (Instrument Units):"
        )
        self.lbl_res.grid(row=1, column=2, padx=(10,0), pady=5, sticky="ew", columnspan=1)
        self.ent_res = customtkinter.CTkEntry(
            master = self,
            width = 50,
            height = 28,
            textvariable = tkinter.StringVar(master=self, value=PARAMS_RES)
        )
        self.ent_res.grid(row=1, column=3, padx=(10,10), pady=5, sticky="ew", columnspan=1)
        # set preview and commence buttons
        self.btn_prv = customtkinter.CTkButton(
            master = self,
            text = "Preview Scheme",
            command = self.app_prv,
            fg_color = "transparent",
            border_width = 1,
            hover_color = "gray23"
        )
        self.btn_prv.grid(row=2, column=0, padx=10, pady=5, sticky="ew", columnspan=4)
        self.btn_cmc = customtkinter.CTkButton(master=self, text="Commence", command=self.app_exp)
        self.btn_cmc.grid(row=3, column=0, padx=10, pady=(5,10), sticky="ew", columnspan=4)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on call ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def app_prv(self, prev: bool = True, save: bool = False):
        """
        Function: get a preview of the scan scheme with pyplot.
        """
        rtn = []
        itr = 0
        # for all the entry frames created
        for i in range(1, len(self.frm_lst.frames)):
            # get user inputs from entries
            try:
                rtn.append(
                    scheme_create_global(
                        float(self.frm_lst.frames[i].inp_minx.get()),
                        float(self.frm_lst.frames[i].inp_maxx.get()),
                        float(self.frm_lst.frames[i].inp_miny.get()),
                        float(self.frm_lst.frames[i].inp_maxy.get()),
                        bool(self.frm_lst.frames[i].inp_pfs.get()),
                        PARAMS_RES
                    )
                )
                itr += len(rtn[i-1][0])
            except ValueError:
                print("Warning: user input with noncompliant format.")
                return ([],[],[])
        return scheme_export_packed(rtn, self.ent_pth.get(), int(self.ent_res.get()), prev, save)
    # ---------------------------------------------------------------------------------------------
    def app_exp(self):
        """
        Function: commence the export of collected user inputs.
        """
        self.rtn = self.app_prv(False, True)
        self.quit()


class Lst(customtkinter.CTkScrollableFrame):
    """
    Class: ctk scrolable frame containing all subgroup entries.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        # --------------------------------- initialize frame list ---------------------------------
        # initialize an entry list
        self.frames = []
        # initialize append button
        self.btn_apd = customtkinter.CTkButton(
            master = self,
            width = 850,
            text = "+",
            command = self.lst_add
        )
        self.btn_apd.grid(row=0, column=0, padx=5, pady=5, sticky="ew", columnspan=1)
        self.frames.append(self.btn_apd)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on call ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def lst_add(self):
        """
        Function: add a new subgroup entry at the bottom frame.
        """
        # initialize the new entry
        ent_new = Ent(master=self, item=len(self.frames), fg_color="grey32")
        ent_new.grid(row=len(self.frames), column=0, padx=5, pady=5, sticky="ew", columnspan=1)
        # add this entry to frames
        self.frames.append(ent_new)
    # ---------------------------------------------------------------------------------------------
    def lst_rmv(self, item):
        """
        Function: remove the entry that initiated the function.
        
        item : an Ent class entry frame initiated the function.
        """
        for ent in self.frames:
            if ent is item:
                ent.destroy()
                self.frames.remove(ent)
        for i in range(1, len(self.frames)):
            self.frames[i].lbl_itr.configure(True, text=i)
            self.frames[i].grid(row=i)
    # ---------------------------------------------------------------------------------------------
    def lst_swp(self, item, dirc):
        """
        Function: swap the entry order of two adjacent entries.
        """
        # find the target position of the swap based on direction
        for i in range(1, len(self.frames)):
            if self.frames[i] is item:
                # if index overflows after the swap, return early
                if dirc == "up":
                    if i > 1:
                        itr = i
                        # break the loop once the target is found
                        break
                    return
                if dirc == "down":
                    if i < len(self.frames) - 1:
                        itr = i+1
                        break
                    return
        # from the target position, move all trailing frames down
        for j in range(itr-1, len(self.frames)):
            if j != itr:
                self.frames[j].grid(row=j+1)
            else:
                self.frames[j].grid(row=j-1)
        # swap the target frame with the frame that sets above it
        tmp = self.frames[itr]
        self.frames[itr] = self.frames[itr-1]
        self.frames[itr-1] = tmp
        # revise label numbers for all entries in the frames list
        for i in range(1, len(self.frames)):
            self.frames[i].lbl_itr.configure(True, text=i)
            self.frames[i].grid(row=i)


class Ent(customtkinter.CTkFrame):
    """
    Class: ctk frame for one subgroup entry storing user input.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, master, item, **kwargs):
        super().__init__(master, **kwargs)
        # ------------------------------ initialize frame GUI layout ------------------------------
        # initialize marking label
        self.lbl_itr = customtkinter.CTkLabel(master=self, width=28, text=f"{item}")
        self.lbl_itr.grid(row=0, column=0, padx=5, pady=5)
        # create input entry boxes
        self.inp_minx = customtkinter.CTkEntry(master=self, width=120, placeholder_text="Min X")
        self.inp_minx.grid(row=0, column=1, padx=5, pady=5)
        self.inp_maxx = customtkinter.CTkEntry(master=self, width=120, placeholder_text="Max X")
        self.inp_maxx.grid(row=0, column=2, padx=5, pady=5)
        self.inp_miny = customtkinter.CTkEntry(master=self, width=120, placeholder_text="Min Y")
        self.inp_miny.grid(row=0, column=3, padx=5, pady=5)
        self.inp_maxy = customtkinter.CTkEntry(master=self, width=120, placeholder_text="Max Y")
        self.inp_maxy.grid(row=0, column=4, padx=5, pady=5)
        self.inp_pfs = customtkinter.CTkCheckBox(master=self, width=120, text="Enable PFS")
        self.inp_pfs.grid(row=0, column=5, padx=(5,25), pady=5)
        # create extra option menu
        self.btn_mup = customtkinter.CTkButton(
            master = self,
            width = 28,
            text = "▴",
            command = lambda: master.lst_swp(self, "up"),
            fg_color = "transparent",
            border_width = 1,
            hover_color = "gray23"
        )
        self.btn_mup.grid(row=0, column=6, padx=5, pady=5)
        self.btn_mdn = customtkinter.CTkButton(
            master = self,
            width = 28,
            text = "▾",
            command = lambda: master.lst_swp(self, "down"),
            fg_color = "transparent",
            border_width = 1,
            hover_color = "gray23"
        )
        self.btn_mdn.grid(row=0, column=7, padx=5, pady=5)
        self.btn_rmv = customtkinter.CTkButton(
            master = self,
            width = 28,
            text = "-",
            command = lambda: master.lst_rmv(self),
            fg_color = "transparent",
            border_width = 1,
            hover_color = "#B62B24"
        )
        self.btn_rmv.grid(row=0, column=8, padx=5, pady=5)


# ====================================== scheme construction ======================================

def scheme_export_packed(
        scheme_l: list,             # the list of scan schemes to be merged
        scheme_p: str = "",         # file save path for the exported image
        scheme_d: int = None,       # dimension of FOV scans in given units
        scheme_r: bool = True,      # preview scan scheme in pyplot if true
        scheme_s: bool = False      # save new folders and csv file if true
):
    """
    ### Return a list of xy pairs, a list of autofocus schemes, and a list of image paths.

    `l` : the list of scan schemes to be merged.
    ----------------------------------------------------------------------------------------------
    #### Optional:
    `p` : file save path for the exported image = `""`.
    `d` : dimension of FOV scans in given units = `None`.
    `r` : preview scan scheme in pyplot if true = `False`.
    `s` : save new folders and csv file if true = `False`.
    """
    lst = []
    fcs = []
    pth = []
    txt = ""
    loc = os.path.join(scheme_p, "_latest")
    # append all coordinate pairs in all schemes stored in scheme_l
    for i, scheme in enumerate(scheme_l):
        # create a folder for each subgroup, skip if not successful
        if scheme_s is True:
            try:
                os.makedirs(os.path.join(loc, f"Subgroup {i+1}"))
            except FileExistsError:
                print(f"Warning: overwriting contents at {loc}.")
        # append coordinates and autofocus parameters for returning
        for j in range(0, len(scheme[0])):
            pth.append(os.path.join(loc, f"Subgroup {i+1}"))
            lst.append(scheme[0][j])
            if scheme[1] == 0:
                fcs.append(0)
            elif scheme[2] is True:
                if j != 0:
                    fcs.append(0)
                else:
                    fcs.append(scheme[1])
            else:
                fcs.append(scheme[1])
    # append parameters into an f-string for previewing on the side
    txt += f"Number of Subgroups: {len(scheme_l)}\n"
    txt += f"Number of Scans: {len(lst)}\n"
    if scheme_d is not None:
        txt += f"Scan Dimension: {scheme_d} IU\n"
        # display warning if dimension <= 0, but do not raise error
        if scheme_d <= 0:
            txt += "    - Current Scan Resolution May Cause Error.\n"
    txt += f"\nImage Save Path: {scheme_p}\n"
    txt += "    - Green: standard scan.\n"
    txt += "    - Blue: autofocused scan."
    # graph all saved items for scheme preview in a separate window
    if scheme_r is True:
        plt.text(
            x = 1.05,
            y = 1,
            s = txt,
            transform = plt.gca().transAxes,
            fontsize = 10,
            verticalalignment='top',
            bbox = dict(facecolor='none', alpha=0.15)
            )
        plt.gca().set_aspect('equal')
        plt.gcf().set_figwidth(15)
        plt.gcf().set_figheight(7.5)
        plt.tight_layout()
        plt.show()
    else:
        plt.close("all")
    # create folders and csv file for coordinate pairs if necessary
    if scheme_s is True:
        # create new csv or overwrite existing csv file in scheme_p
        path = os.path.join(loc, PARAMS_RTN)
        df = pd.DataFrame({'x':[], 'y':[], 'z':[]})
        df.to_csv(path)
    return (lst, fcs, pth)


def scheme_create_global(
        min_x: float,
        max_x: float,
        min_y: float,
        max_y: float,
        scan_pfs: bool,
        scan_res: float,
):
    """
    ### Return a tuple of xy coordinates and the autofocus scheme, passing a plot preview.

    `min_x` : minimum x value (left).
    `max_x` : maximum x value (right).
    `min_y` : minimum y value (down).
    `max_y` : maximum y value (up).
    `scan_pfs` : if Nikon PFS will be activated.
    `scan_res` : scan resolution of each image (IU or um).
    """
    # make sure scan resolution is constant and always positive
    RES = abs(scan_res)
    # make sure PFS setting is constant
    PFS = scan_pfs
    FOCUS_M = 2 if PFS else 0
    # find center coordinates, tissue ranges, and scan dimensions
    CENTER_X = round((max_x + min_x) / 2)   # must be int
    CENTER_Y = round((max_y + min_y) / 2)   # must be int
    RANGE_X = abs(max_x - min_x)            # must be positive
    RANGE_Y = abs(max_y - min_y)            # must be positive
    DIM_X = math.ceil(RANGE_X / RES)        # must be int
    DIM_Y = math.ceil(RANGE_Y / RES)        # must be int
    # initialize local variables
    current_x = 0
    current_y = 0
    current_i = 0
    rtn = []
    # find start coordinates (on the top-left corner) of the tissue
    current_x = CENTER_X - math.floor(DIM_X / 2) * RES
    current_y = CENTER_Y + math.floor(DIM_Y / 2) * RES
    # loop through all imaging positions (in an S-shape order)
    # append xy coordinates, pfs, and store a preview into pyplot
    for row in range(0, DIM_Y):
        # in every row, only loop to the second last image
        for _ in range(0, (DIM_X-1)):
            # first append the image's coordinates
            rtn.append([current_x, current_y])
            # store a preview area in pyplot
            pyplot_create_region(
                current_x,
                current_y,
                RES,
                RES,
                c = 'b' if PFS else 'g',
                e = 'b' if PFS else 'g',
                i = current_i
            )
            # then, move the coordinates based on which row it sits
            if row % 2 == 0:
                # if it's an even number row, move to the right
                current_x += RES
            else:
                # if it's an odd number row, move to the left
                current_x -= RES
            # increment the number of images taken
            current_i += 1
        # now the xy coordinates are parked at the last image of the row
        # append the current xy coordinates to save this last image
        rtn.append([current_x, current_y])
        # store a preview area in pyplot
        pyplot_create_region(
            current_x,
            current_y,
            RES,
            RES,
            c = 'b' if PFS else 'g',
            e = 'b' if PFS else 'g',
            i = current_i
        )
        # then instead of moving the x coordinate, move the y coordinate
        # this will move the current xy coordinates to the next row
        current_y -= RES
        # increment the number of images taken
        current_i += 1
    # return compiled xy coordinates and autofocus methods
    # the format is held constant with `scheme_create_subgrp` function
    return (rtn, FOCUS_M, False)


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
    plt.text(x, y, i, ha=f, va=v, alpha=a)
    # plot j as image and rectX - rectY as lines
    if j != "":
        # open image with PIL
        img = Image.open(j)
        # flip image if needed
        if b is True:
            img = img.transpose(method=Image.Transpose.FLIP_LEFT_RIGHT)
        if d is True:
            img = img.transpose(method=Image.Transpose.FLIP_TOP_BOTTOM)
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


def csvset_modify_concat(
        file_path,
        new_value,
        file_name = PARAMS_RTN,
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
    df1 = pd.concat([df1, df2], ignore_index=True)
    df1.to_csv(file_path, index=False)


# ========================================= main function =========================================

def mercury_01(
        _ = None
):
    """
    Main application loop of mercury 01, return user inputs when loop ended.
    """
    # set customtkinter appearance mode and color theme
    customtkinter.set_appearance_mode("dark")
    customtkinter.set_default_color_theme("blue")
    # enter main loop and return user inputs when ended
    app = App()
    app.resizable(False, False)
    app.mainloop()
    try:
        return app.rtn
    except AttributeError:
        return ([],[],[])
