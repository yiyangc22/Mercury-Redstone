"""
Mercury 05: blocker prep constructor, project version 1.2 (with python 3.9).
"""

import math
import tkinter as tk
import customtkinter

WINDOW_TXT = "Mercury V - Blocker Fluidic Procedure"
WINDOW_RES = "600x120"
PARAMS_PRT = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
              "11","12","13","14","15","16","17","18","19","21",
              "22","23","24"]
PARAMS_BL1 = 500
PARAMS_BL2 = 200
PARAMS_BL3 = 900


# ===================================== customtkinter classes =====================================

class Moa:
    """
    Class: mother of all classes, parent and pass inputs from customtkinter.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self):
        super().__init__()
        self.rtn = (1,0,0,0)

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
        self.rtn = (1,0,0,0)
        # -------------------------------------- GUI setting --------------------------------------
        self.lbl_prt = customtkinter.CTkLabel(
            master = self,
            width = 150,
            height = 30,
            anchor = "w",
            text = "  Blocker Port:"
        )
        self.lbl_prt.grid(row=0, column=0, padx=(10,5), pady=(10,0))
        self.inp_prt = customtkinter.CTkComboBox(
            master = self,
            width = 150,
            height = 30,
            values = PARAMS_PRT
        )
        self.inp_prt.grid(row=1, column=0, padx=(10,5), pady=5)
        self.lbl_bl1 = customtkinter.CTkLabel(
            master = self,
            width = 150,
            height = 30,
            anchor = "w",
            text = "  Flow Rate (uL/min):"
        )
        self.lbl_bl1.grid(row=0, column=1, padx=5, pady=(10,0))
        self.inp_bl1 = customtkinter.CTkEntry(
            master = self,
            width = 150,
            height = 30,
            textvariable = tk.StringVar(master=self, value=PARAMS_BL1)
        )
        self.inp_bl1.grid(row=1, column=1, padx=5, pady=5)
        self.lbl_bl2 = customtkinter.CTkLabel(
            master = self,
            width = 150,
            height = 30,
            anchor = "w",
            text = "  Flow Volume (uL):"
        )
        self.lbl_bl2.grid(row=0, column=2, padx=5, pady=(10,0))
        self.inp_bl2 = customtkinter.CTkEntry(
            master = self,
            width = 150,
            height = 30,
            textvariable = tk.StringVar(master=self, value=PARAMS_BL2)
        )
        self.inp_bl2.grid(row=1, column=2, padx=5, pady=5)
        self.lbl_bl3 = customtkinter.CTkLabel(
            master = self,
            width = 150,
            height = 30,
            anchor = "w",
            text = "  Wait Time (s):"
        )
        self.lbl_bl3.grid(row=0, column=3, padx=(5,10), pady=(10,0))
        self.inp_bl3 = customtkinter.CTkEntry(
            master = self,
            width = 150,
            height = 30,
            textvariable = tk.StringVar(master=self, value=PARAMS_BL3)
        )
        self.inp_bl3.grid(row=1, column=3, padx=(5,10), pady=5)
        self.btn_cmc = customtkinter.CTkButton(master=self, text="Commence", command=self.app_exp)
        self.btn_cmc.grid(row=2, column=0, padx=10, pady=(5,10), sticky="nesw", columnspan=4)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on call ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def app_exp(self):
        """
        Function: commence the export of collected user inputs.
        """
        rtn = self.rtn
        try:
            rtn = (
                math.floor(abs(float(self.inp_prt.get()))),
                math.floor(abs(float(self.inp_bl1.get()))),
                math.floor(abs(float(self.inp_bl2.get()))),
                math.floor(abs(float(self.inp_bl3.get())))
            )
        except ValueError:
            print("Warning: parameter format error, check parameter inputs.")
        # return results by saving rtn
        self.rtn = rtn
        self.quit()


# ========================================= main function =========================================

def mercury_05():
    """
    Main application loop of mercury 05, display constructed pyplot preview.
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
        return (1,0,0,0)
