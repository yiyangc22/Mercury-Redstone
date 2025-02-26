"""
Mercury 04: image stitching previews, project version 1.2 (with python 3.9).
"""

import os
import tkinter as tk
import pandas as pd
import customtkinter
import matplotlib.pyplot as plt
from mercury_01 import pyplot_create_region

WINDOW_TXT = "Mercury IV - Image Stitching Preview"
WINDOW_RES = "800x100"
PARAMS_RES = 366
PARAMS_RTN = "_coordinates.csv"
PARAMS_AFX = [".tif", ".png", "_2P.png"]


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
        self.inp_exp = customtkinter.CTkEntry(
            master = self,
            width = 105,
            height = 30,
            textvariable = tk.StringVar(master=self, value="_latest")
        )
        self.inp_exp.grid(row=0, column=0, padx=(10,5), pady=5, sticky="ew")
        self.inp_typ = customtkinter.CTkComboBox(
            master = self,
            width = 105,
            height = 30,
            values = PARAMS_AFX
        )
        self.inp_typ.grid(row=0, column=1, padx=(5,5), pady=5)
        self.inp_res = customtkinter.CTkEntry(
            master = self,
            width = 105,
            height = 30,
            textvariable = tk.StringVar(master=self, value=PARAMS_RES)
        )
        self.inp_res.grid(row=0, column=2, padx=(5,10), pady=5)
        self.btn_prv = customtkinter.CTkButton(
            master = self,
            width = 380,
            height = 30,
            text = "Preview",
            command = self.app_exp
        )
        self.btn_prv.grid(row=1, column=0, padx=10, pady=5, sticky="nesw", columnspan=3)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on call ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def app_exp(self):
        """
        Function: commence preview and close.
        """
        preview(self.inp_exp.get(), self.inp_typ.get(), int(self.inp_res.get()))
        self.quit()


# ===================================== independent functions =====================================

def preview(exp, typ, res):
    """
    Function: construct pyplot preview
    """
    # subgroup with tif images
    folder = os.path.join(os.path.expanduser("~"), "Desktop", exp)
    # .csv coordinates
    coords = os.path.join(os.path.expanduser("~"), "Desktop", exp, PARAMS_RTN)
    # read folder, save image paths in list, and print
    images = []
    with os.scandir(folder) as entries:
        for entry in entries:
            if entry.is_dir():
                for file in os.listdir(entry):
                    if file[-len(typ):] == typ:
                        images.append(os.path.join(folder, entry, file))
    # read .csv, save xy coordinates in list, and print
    csv = pd.read_csv(coords).values.tolist()
    coords = []
    for row in csv:
        # invert x (row[1]) or y (row[2]) axis here
        coords.append([row[1], row[2]])
    # create regions in matplotlib based on the coordinates
    for i, coord in enumerate(coords):
        pyplot_create_region(
            coord[0],
            coord[1],
            res if typ != PARAMS_AFX[1] else (res * (1906/2304)),
            res if typ != PARAMS_AFX[1] else (res * (2270/2304)),
            i = i,
            j = images[i],
            a = 0.5,
            b = True if typ == PARAMS_AFX[1] else False,
            d = False,
            r = 90 if typ == PARAMS_AFX[1] else 180
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
    app = App()
    app.resizable(False, False)
    app.mainloop()
