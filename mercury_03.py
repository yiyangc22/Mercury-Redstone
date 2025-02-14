"""
Mercury 03: fluid scheme constructor, project version 1.2 (with python 3.9).
"""

import os
import tkinter
import pandas
import numpy as np
import customtkinter
from PIL import Image

WINDOW_TXT = "Mercury III - Fluid Scheme Constructor"
WINDOW_RES = "900x100"
PARAMS_DTP = os.path.join(os.path.expanduser("~"), "Desktop")               # desktop folder path
PARAMS_DFT = os.path.join(PARAMS_DTP, "_latest")                            # default folder path
PARAMS_LOG = os.path.join(PARAMS_DFT, "data.csv")


# ===================================== customtkinter classes =====================================

class Moa:
    """
    Class: mother of all classes, parent and pass inputs from customtkinter.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self):
        super().__init__()
        self.rtn = ([],[],[])


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
        self.frm_ctl = Apd(master=self)
        self.frm_ctl.grid(row=0, column=0, padx=10, pady=(10,5), sticky="nesw", columnspan=1)
        self.btn_cmc = customtkinter.CTkButton(master=self, text="Commence", command=self.app_exp)
        self.btn_cmc.grid(row=1, column=0, padx=10, pady=(5,10), sticky="nesw", columnspan=1)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on call ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def app_exp(self):
        """
        Function: commence the export of collected user inputs.
        """
        rtn = get_csv(self.frm_ctl.ent_pth.get())
        self.rtn = rtn
        self.quit()


class Apd(customtkinter.CTkFrame):
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
            text = "Experiment Log File (data.csv):"
        )
        self.lbl_pth.grid(row=0, column=0, padx=(10,0), pady=5, sticky="nsew")
        self.ent_pth = customtkinter.CTkEntry(
            master = self,
            width = 650,
            height = 28,
            textvariable = tkinter.StringVar(master=self, value=PARAMS_LOG)
        )
        self.ent_pth.grid(row=0, column=1, padx=(5,10), pady=5, sticky="nsew")


# ===================================== independent functions =====================================

def get_csv(dirc):
    """
    Function: return the content of a designated .csv file in a 2d list.
    """
    rtn = []
    loc = pandas.read_csv(dirc).values.tolist()
    for row in enumerate(loc):
        rtn.append(row)
    return rtn


def get_dtl(path):
    """
    Function: return the last two elements for a file path.
    """
    head, tail1 = os.path.split(path)
    head, tail2 = os.path.split(head)
    return '\\'.join([tail2, tail1])


def get_rtl(path):
    """
    Function: return the path of the folder for input file.
    """
    head, _tail = os.path.split(path)
    return head


def decode_cpmask_tolist(
        original,               # file name with path to the original image
):
    """
    ### Decode a png mask image into LabVIEW compatable 1D list of integers.

    `original` : file name and path to the original images.
    """
    pxl = np.array(Image.open(original)).flatten()
    rtn = []
    for i in pxl:
        if i < 0:
            rtn.append(255)
        else:
            rtn.append(0)
    return rtn


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
        return ([],[],[])
