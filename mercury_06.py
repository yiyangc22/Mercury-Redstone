"""
Mercury 06: single cleave procedures, project version 1.22B (with python 3.9).
"""

import os
import tkinter
import customtkinter

WINDOW_TXT = "Mercury VI - Standalone 2P Cleave"
WINDOW_RES = "670x260"
PARAMS_OTF = os.path.join(os.path.expanduser("~"), "Desktop")
PARAMS_LIN = "2P_test"
PARAMS_MSK = os.path.join(os.path.expanduser("~"), "Desktop", "TempMask", "Checkerboard.png")
PARAMS_SZE = 2.5


# ===================================== customtkinter classes =====================================

class Moa:
    """
    Class: mother of all classes, parent and pass inputs from customtkinter.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self):
        super().__init__()
        self.rtn = ('', '', '', [], PARAMS_SZE)


class App(customtkinter.CTk, Moa):
    """
    Class: main application window and customtkinter main loop.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, x = None, y = None, z = None):
        super().__init__()
        # ---------------------------------- application setting ----------------------------------
        self.title(WINDOW_TXT)
        self.geometry(WINDOW_RES)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        # store input xyz value into ctk app mainloop
        self.x = x
        self.y = y
        self.z = z
        # -------------------------------------- GUI setting --------------------------------------
        self.control = Panel(master=self)
        self.control.grid(row=0, column=0, padx=5, pady=(10,5), sticky="ew")
        self.btn_cmc = customtkinter.CTkButton(master=self, text="Commence", command=self.app_exp)
        self.btn_cmc.grid(row=3, column=0, padx=5, pady=(5,10), sticky="ew")
    # ---------------------------------------------------------------------------------------------
    def app_exp(self):
        """
        Function: commence the export of collected user inputs.
        """
        try:
            out1 = self.control.inp_otfs.get_entry()
            out2 = self.control.inp_lins.get_entry()
            out3 = self.control.inp_mask.get_entry()
            out4 = [
                float(self.control.inp_ctrx.get_entry()),
                float(self.control.inp_ctry.get_entry()),
                float(self.control.inp_ctrz.get_entry()),
            ]
            out5 = float(self.control.inp_scan.get_entry())
            self.rtn = (out1, out2, out3, out4, out5)
            self.quit()
        except ValueError:
            print("Warning: parameter format error, check parameter inputs.")


class Panel(customtkinter.CTkFrame):
    """
    Class: ctk frame for adding individual instrument commands.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        # ------------------------------ initialize frame GUI layout ------------------------------
        # export image folder
        self.inp_otfs = Entry(
            master = self,
            width = 650,
            height = 28,
            label = "  Save Laser Image to Folder:",
            textvar = PARAMS_OTF,
            placeholder = "(Required)"
        )
        self.inp_otfs.grid(row=0, column=0, padx=5, pady=5, columnspan=5)
        # center x
        self.inp_ctrx = Entry(
            master = self,
            width = 105,
            height = 28,
            label = "  Center X",
            textvar = self.master.x,
            placeholder = "(Required)"
        )
        self.inp_ctrx.grid(row=1, column=0, padx=(5,0), pady=5)
        # center y
        self.inp_ctry = Entry(
            master = self,
            width = 105,
            height = 28,
            label = "  Center Y",
            textvar = self.master.y,
            placeholder = "(Required)"
        )
        self.inp_ctry.grid(row=1, column=1, padx=(5,0), pady=5)
        # center z
        self.inp_ctrz = Entry(
            master = self,
            width = 105,
            height = 28,
            label = "  Center Z",
            textvar = self.master.z,
            placeholder = "(Required)"
        )
        self.inp_ctrz.grid(row=1, column=2, padx=(5,0), pady=5)
        # scan size (laser power)
        self.inp_scan = Entry(
            master = self,
            width = 105,
            height = 28,
            label = "  Scan Size",
            textvar = PARAMS_SZE,
            placeholder = "(Required)"
        )
        self.inp_scan.grid(row=1, column=3, padx=(5,0), pady=5)
        # laser image name
        self.inp_lins = Entry(
            master = self,
            width = 206,
            height = 28,
            label = "  Base File Name",
            textvar = PARAMS_LIN,
            placeholder = "(Required)"
        )
        self.inp_lins.grid(row=1, column=4, padx=5, pady=5)
        # Mask Image Full Path
        self.inp_mask = Entry(
            master = self,
            width = 650,
            height = 28,
            label = "  Mask Image Full Path:",
            textvar = PARAMS_MSK,
            placeholder = "(Required)"
        )
        self.inp_mask.grid(row=2, column=0, padx=5, pady=5, columnspan=5)



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
    

# ========================================= main function =========================================

def mercury_06(
        x = None,
        y = None,
        z = None,
):
    """
    Main application loop of mercury 06, return user inputs when loop ended.
    """
    # set customtkinter appearance mode and color theme
    customtkinter.set_appearance_mode("dark")
    customtkinter.set_default_color_theme("blue")
    # enter main loop and return user inputs when ended
    app = App(x, y, z)
    app.resizable(False, False)
    app.mainloop()
    try:
        return app.rtn
    except AttributeError:
        return ('', '', '', [], PARAMS_SZE)
