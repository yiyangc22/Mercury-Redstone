"""
Mercury 03: fluid scheme constructor, project version 1.2 (with python 3.9).
"""

import os
import tkinter as tk
from datetime import date

import pandas as pd
import customtkinter
from PIL import Image, ImageOps

from mercury_01 import open_file_dialog
from mercury_02 import count_non_white_pixel

WINDOW_TXT = "Mercury III - Fluid Scheme Constructor"
WINDOW_RES = "800x100"

PARAMS_DTP = os.path.join(os.path.expanduser("~"), "Desktop")
PARAMS_EXP = os.path.join(PARAMS_DTP, f"latest_{date.today()}")
PARAMS_MCI = "image_multichannel"
PARAMS_MSK = "image_mask"
PARAMS_MAP = "image_cleave_map"
PARAMS_PLN = "coord_planned.csv"
PARAMS_CRD = "coord_recorded.csv"
PARAMS_GLB = "image_mask_global.png"
PARAMS_SCT = "coord_scan_center.csv"
PARAMS_BIT = "config_bit_scheme.csv"
PARAMS_TMP = "image_mask_tmp.png"


# ===================================== customtkinter classes =====================================

class Moa:
    """
    Class: mother of all classes, parent and pass inputs from customtkinter.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self):
        super().__init__()
        self.rtn = ([],'','',[[]])


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
        self.frm_ctl = Exp(master=self)
        self.frm_ctl.grid(row=0, column=0, padx=10, pady=(10,5), sticky="nesw", columnspan=1)
        self.btn_cmc = customtkinter.CTkButton(master=self, text="Commence", command=self.app_exp)
        self.btn_cmc.grid(row=1, column=0, padx=10, pady=(5,10), sticky="nesw", columnspan=1)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on call ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def app_exp(self):
        """
        Function: commence the export of collected user inputs.
        """
        # get user inputs
        path_folder = self.frm_ctl.ent_pth.get()
        path_maskfd = os.path.join(path_folder, PARAMS_MAP)
        path_tmpmsk = os.path.join(path_folder, PARAMS_TMP)
        path_bitsch = os.path.join(path_folder, PARAMS_BIT)
        path_scanct = os.path.join(path_folder, PARAMS_SCT)
        # arrange parameters into labview clusters (tuples)
        port_list = []
        port_length = len(pd.read_csv(
            path_bitsch, keep_default_na = False).values.tolist()[0][8].split(', '))
        for i in range(port_length):
            port_list.append(i+1)
        center_coordinates = pd.read_csv(
            path_scanct, keep_default_na = False, usecols=[1,2,3,4,5,6,7]).values.tolist()
        self.rtn = (port_list, path_maskfd, path_tmpmsk, center_coordinates)
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


# ===================================== independent functions =====================================

def update_mask(img_folder, num_round, area):
    """
    Function: update and stretch temp cleave mask based on round/area number
    return false if the update is unsuccessful
    """
    # check for valid input
    if num_round < 0 or area < 0:
        print(f"Warning: invalid round/area combination: round {num_round} area {area}.")
        print(f"Warning: round {num_round} area {area} not executed.")
        return False
    # try constructing the mask
    try:
        # access cleave center coordinates
        exp_folder = os.path.dirname(img_folder)
        center_coordinates = pd.read_csv(os.path.join(exp_folder, PARAMS_SCT),
            keep_default_na = False, usecols=[4,5,6,7]).values.tolist()[area]
        # access cleave mask area
        tgt_mask = Image.open(os.path.join(img_folder, f"Round {num_round}.png"))
        tgt_mask = tgt_mask.crop(center_coordinates)
        # if the designated area is (nearly) blank, drop this area and return
        px_threshold = 10
        if count_non_white_pixel(tgt_mask) < px_threshold:
            print(f"Warning: designated area's pixel count is lower than {px_threshold}.")
            print(f"Warning: round {num_round} area {area} not executed.")
            return False
        # modify cleave mask
        # first create a [366, 366] empty mask
        mod_mask = Image.new('P', [732,732], color = (255,255,255))
        # then paste the [300, 300] cleave mask to the center
        bg_width, bg_height = mod_mask.size
        overlay_width, overlay_height = tgt_mask.size
        x_center = round((bg_width - overlay_width) / 2)
        y_center = round((bg_height - overlay_height) / 2)
        mod_mask.paste(tgt_mask, (x_center, y_center))
        # stretch the modified mask to [2304, 2304]
        mod_mask = mod_mask.resize([2304, 2304])
        # crop out laser area
        mod_mask = mod_mask.crop((208, 34, 1906, 2270))
        # flip vertically, then rotate 90 degrees to the left
        mod_mask = mod_mask.transpose(Image.Transpose.FLIP_TOP_BOTTOM).rotate(-90)
        # save the modified image as the new temp mask
        rtn_mask = mod_mask.resize([1024, 1024]).convert('L')
        rtn_mask = ImageOps.invert(rtn_mask)
        rtn_mask.save(os.path.join(exp_folder, PARAMS_TMP), format='PNG')
        return True
    except FileNotFoundError as e:
        print(f"Warning: {e}")
        print(f"Warning: round {num_round} area {area} not executed.")
        return False


# ========================================= main function =========================================

def mercury_03():
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
        return ([],'','',[[]])
