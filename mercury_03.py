"""
Mercury 03: fluid scheme constructor, project version 1.2 (with python 3.9).
"""

import os
import tkinter as tk
from datetime import date

import pandas
import customtkinter

from mercury_01 import open_file_dialog

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
        self.rtn = ([],'','')


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
        path_folder = self.frm_ctl.ent_pth.get()
        path_maskfd = os.path.join(path_folder, PARAMS_MAP)
        path_tmpmsk = os.path.join(path_folder, PARAMS_TMP)
        center_coordinates = pandas.read_csv(
            os.path.join(path_folder, PARAMS_SCT),
            keep_default_na = False).values.tolist()
        self.rtn = (center_coordinates, path_maskfd, path_tmpmsk)
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
        return ([],'','')
