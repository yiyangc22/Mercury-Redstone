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
        # variable set up, read csv file
        rtn = ([],[],[])
        csv = get_csv(self.frm_ctl.ent_pth.get())
        # check if there are null values in the command list
        # then, arrange csv data into compatable format
        for entry in csv:
            # assume all commands are valid
            cmd = [True, True, True]
            # check if entry has parameters for laser procedure
            for i in range(0, 5):
                if entry[i] == '' or entry[i] == 'null':
                    cmd[0] = False
                    break
            # check if entry has parameters for fluidic procedure
            for i in range(5, 8):
                if entry[i] == '' or entry[i] == 'null':
                    cmd[1] = False
                    break
            # check if entry has parameters for wait procedure
            if entry[8] == '' or entry[8] == 'null':
                cmd[2] = False
            # append commands into rtn in rearranged format
            #######################################################################################
            #######################################################################################
            # if the row is completely filled (full experiment run), append full fluidic procedures
            if cmd[0] and cmd[1] and cmd[2]:
                # ---------------------------------------------------------------------------------
                # ligase buffer wash
                rtn[0].append(2)
                rtn[1].append([24.0, 500.0, 500.0])
                rtn[2].append('')
                # ---------------------------------------------------------------------------------
                # 2p cleave laser
                if entry[4] == 0:
                    rtn[0].append(0)
                else:
                    rtn[0].append(1)
                rtn[1].append([float(entry[0]), float(entry[1]), float(entry[2])])
                rtn[2].append(entry[3])
                # ---------------------------------------------------------------------------------
                # ligation buffer wash
                rtn[0].append(2)
                rtn[1].append([24.0, 500.0, 500.0])
                rtn[2].append('')
                # ---------------------------------------------------------------------------------
                # ligagion reaction (active)
                rtn[0].append(2)
                rtn[1].append([float(entry[5]), float(entry[6]), float(entry[7])])
                rtn[2].append('')
                # ---------------------------------------------------------------------------------
                # wait (ligation time)
                rtn[0].append(3)
                rtn[1].append([float(entry[8]), 0.0, 0.0])
                rtn[2].append('')
                # ---------------------------------------------------------------------------------
                # DPBS wash
                rtn[0].append(2)
                rtn[1].append([23.0, 500.0, 1000.0])
                rtn[2].append('')
            #######################################################################################
            #######################################################################################
            # if a row does not include parameters needed for a full experiment run
            else:
                # for laser procedures
                if cmd[0]:
                    # append command type to rtn[0]
                    if entry[4] == 0:
                        rtn[0].append(0)
                    else:
                        rtn[0].append(1)
                    # append laser coordinates to rtn[1]
                    rtn[1].append([float(entry[0]), float(entry[1]), float(entry[2])])
                    # append mask directory to rtn[2]
                    rtn[2].append(entry[3])
                # for fluidic procedures
                if cmd[1]:
                    # append command type to rtn[0]
                    rtn[0].append(2)
                    # append fluidic parameters to rtn[1]
                    rtn[1].append([float(entry[5]), float(entry[6]), float(entry[7])])
                    # append empty string to rtn[2]
                    rtn[2].append('')
                # for wait procedures
                if cmd[2]:
                    # append command type to rtn[0]
                    rtn[0].append(3)
                    # append wait parameter to rtn[1]
                    rtn[1].append([float(entry[8]), 0.0, 0.0])
                    # append empty string to rtn[2]
                    rtn[2].append('')
        # return results by saving rtn
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
    loc = pandas.read_csv(dirc, keep_default_na=False).values.tolist()
    for row in enumerate(loc):
        rtn.append(row[1][1:])
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
