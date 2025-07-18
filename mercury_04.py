"""
Mercury 04: image stitching previews, project version 1.2 (with python 3.9).
"""

import os
import tkinter as tk
from datetime import date

import customtkinter
import matplotlib.pyplot as plt

from mercury_01 import pyplot_create_region, open_file_dialog
from mercury_02 import read_xycoordinates

WINDOW_TXT = "Mercury IV - Image Stitching Preview"
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
        self.frm_ctl.grid(row=0, column=0, padx=10, pady=(10,5), sticky="nesw", columnspan=4)
        self.btn_cmc = customtkinter.CTkButton(
            master = self,
            text = "Stitch Multichannel Images",
            command = self.app_cmc_mlt
        )
        self.btn_cmc.grid(row=1, column=0, padx=10, pady=(5,10), sticky="nesw", columnspan=1)
        self.btn_cmc = customtkinter.CTkButton(
            master = self,
            text = "Stitch Laser Masks",
            command = self.app_cmc_msk
        )
        self.btn_cmc.grid(row=1, column=1, padx=(0,10), pady=(5,10), sticky="nesw", columnspan=1)
        self.btn_cmc = customtkinter.CTkButton(
            master = self,
            text = "Stitch Laser Images",
            command = self.app_cmc_lsr
        )
        self.btn_cmc.grid(row=1, column=2, padx=(0,10), pady=(5,10), sticky="nesw", columnspan=1)
        self.ent_rnd = customtkinter.CTkEntry(
            master = self,
            placeholder_text = "(Round Number)"
        )
        self.ent_rnd.grid(row=1, column=3, padx=(0,10), pady=(5,10), sticky="nesw", columnspan=1)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on call ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def app_cmc_mlt(self):
        """
        Function: preview stitching for multichannel images.
        """
        # acquire image paths
        file_endswith = '.tif'
        file_location = os.path.join(self.frm_ctl.ent_pth.get(), PARAMS_MCI)
        images = []
        for file in os.listdir(file_location):
            if file[-len(file_endswith):] == file_endswith:
                images.append(os.path.join(file_location, file))
        # acquire multichannel coordinates
        file_location = os.path.join(self.frm_ctl.ent_pth.get(), PARAMS_PLN)    # or PARAMS_CRD
        coords = read_xycoordinates(file_location)
        # check list lengths, initiate preview
        if len(images) != len(coords):
            print(f"Warning: found {len(images)} images, {len(coords)} coordinate pairs.")
            return
        preview_stitching(images, coords, 366, 366, 180)
    # ---------------------------------------------------------------------------------------------
    def app_cmc_msk(self):
        """
        Function: preview stitching for laser masks.
        """
        # acquire image paths
        file_endswith = '.png'
        file_location = os.path.join(self.frm_ctl.ent_pth.get(), PARAMS_MSK)
        images = []
        for file in os.listdir(file_location):
            if file[-len(file_endswith):] == file_endswith:
                images.append(os.path.join(file_location, file))
        # acquire multichannel coordinates
        file_location = os.path.join(self.frm_ctl.ent_pth.get(), PARAMS_PLN)    # or PARAMS_CRD
        coords = read_xycoordinates(file_location)
        # check list lengths, initiate preview
        if len(images) != len(coords):
            print(f"Warning: found {len(images)} images, {len(coords)} coordinate pairs.")
            return
        preview_stitching(images, coords, 366, 366, 180)
    # ---------------------------------------------------------------------------------------------
    def app_cmc_lsr(self):
        """
        Function: preview stitching for laser images.
        """
        # acquire round number and image paths, return if error is encountered
        try:
            num_round = int(self.ent_rnd.get())
            file_endswith = '.tif'
            file_location = os.path.join(self.frm_ctl.ent_pth.get(), PARAMS_MAP)
            images = []
            texts = []
            for file in os.listdir(file_location):
                if file[-len(file_endswith):] == file_endswith:
                    file_prefix_num = int(file[0:4]) - 1000
                    if file_prefix_num == num_round:
                        images.append(os.path.join(file_location, file))
                        texts.append(file_prefix_num)
            if len(images) == 0:
                print(f"Warning: found no laser images with matching round number {num_round}.")
                return
        except (ValueError, TypeError) as e:
            print(f"Warning: {e}")
            return
        # acquire multichannel coordinates
        file_location = os.path.join(self.frm_ctl.ent_pth.get(), PARAMS_SCT)
        coords = read_xycoordinates(file_location)
        # check list lengths, initiate preview
        if len(images) != len(coords):
            print(f"Warning: found {len(images)} images, {len(coords)} coordinate pairs.")
            return
        preview_stitching(
            images,
            coords,
            366,
            366,
            rotation = 90,
            flip_left_right = True,
            center_text = texts
        )


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

def preview_stitching(
        images: list,
        coords: list,
        width,
        height,
        rotation = 0,
        center_text = None,
        flip_top_bottom = False,
        flip_left_right = False
    ):
    """
    Function: construct pyplot preview for listed images and coordinates.
    """
    # determine center text values
    # case 1: display a string
    if isinstance(center_text, str):
        text_mode = 1
    # case 2: display contents of a list
    elif isinstance(center_text, list):
        text_mode = 2
    # case 0: display none ("")
    else:
        text_mode = 0
    # initialize pyplot regions
    for i, coord in enumerate(coords):
        pyplot_create_region(
            coord[0],
            coord[1],
            width,
            height,
            i = "" if text_mode == 0 else (i if text_mode == 1 else center_text[i]),
            j = images[i],
            g = 0.5,
            r = rotation,
            d = flip_top_bottom,
            b = flip_left_right
        )
    plt.gca().set_aspect('equal')
    plt.gcf().set_figheight(10)
    plt.gcf().set_figwidth(10)
    plt.show()


# ========================================= main function =========================================

def mercury_04():
    """
    Main application loop of mercury 04, display constructed pyplot preview.
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
