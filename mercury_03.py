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
WINDOW_RES = "900x600"
PARAMS_DTP = os.path.join(os.path.expanduser("~"), "Desktop")               # desktop folder path
PARAMS_DFT = os.path.join(PARAMS_DTP, "_latest")                            # default folder path
PARAMS_CSV = os.path.join(PARAMS_DFT, "_coordinates.csv")                   # default coordinates
PARAMS_CMD = ["Laser", "Fluidic", "Wait", "All"]                            # instrument commands
PARAMS_LSR = ["2P", "2P+Img"]                                               # laser mask commands


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
        # create the scrollable frame list
        self.frm_lst = Lst(master=self, corner_radius=5)
        self.frm_lst.grid(row=0, column=0, padx=10, pady=5, sticky="nsew", columnspan=2)
        self.btn_cmc = customtkinter.CTkButton(master=self, text="Commence", command=self.app_exp)
        self.btn_cmc.grid(row=3, column=0, padx=10, pady=(5,10), sticky="nesw", columnspan=2)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on call ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def app_exp(self):
        """
        Function: commence the export of collected user inputs.
        """
        rtn = ([],[],[])
        for itm in self.frm_lst.frames:
            try:
                if itm.lbl_typ.cget("text") == PARAMS_CMD[0]:
                    if itm.inp_drp.get() == PARAMS_LSR[0]:
                        rtn[0].append(0)
                    elif itm.inp_drp.get() == PARAMS_LSR[1]:
                        rtn[0].append(1)
                    elif itm.inp_drp.get() == PARAMS_LSR[2]:
                        rtn[0].append(-1)
                    rtn[1].append([
                        float(itm.inp_ctx.get()),
                        float(itm.inp_cty.get()),
                        float(itm.inp_ctz.get())
                    ])
                    rtn[2].append(os.path.join(
                        self.frm_lst.frm_apd.ent_pth.get(),
                        itm.inp_dms.get()
                    ))
                elif itm.lbl_typ.cget("text") == PARAMS_CMD[1]:
                    rtn[0].append(2)
                    rtn[1].append([
                        float(itm.inp_prt.get()),
                        float(itm.inp_flw.get()),
                        float(itm.inp_vol.get())
                    ])
                    rtn[2].append("")
                elif itm.lbl_typ.cget("text") == PARAMS_CMD[2]:
                    rtn[0].append(3)
                    rtn[1].append([float(itm.inp_tim.get()),0.0,0.0])
                    rtn[2].append("")
            except ValueError:
                low = min(len(rtn[0]), len(rtn[1]), len(rtn[2]))
                for lst in rtn:
                    if len(lst) > low:
                        lst.pop(len(lst)-1)
                print(f"MISSING VALUE APPENDING COMMAND #{low+1}")
        self.rtn = rtn
        self.quit()


class Lst(customtkinter.CTkScrollableFrame):
    """
    Class: ctk scrolable frame containing all subgroup entries.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        # --------------------------------- initialize frame list ---------------------------------
        # initialize an empty command list
        self.frames = []
        # create appending/importing frame
        self.frm_apd = Apd(master=self, fg_color="grey23")
        self.frm_apd.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.frames.append(self.frm_apd)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on call ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def lst_add(self, inst, inp1=None, inp2=None, inp3=None):
        """
        Function: add a new subgroup entry at the bottom frame.
        """
        frm_new = None
        if inst == PARAMS_CMD[0]:
            frm_new = Lsr(master=self, item=len(self.frames), cord=inp1, mask=inp2, uses=inp3)
        elif inst == PARAMS_CMD[1]:
            frm_new = Flu(master=self, item=len(self.frames), port=inp1, rate=inp2, volm=inp3)
        elif inst == PARAMS_CMD[2]:
            frm_new = Pse(master=self, item=len(self.frames), time=inp1)
        else:
            for i in range(len(PARAMS_CMD)-1):
                self.lst_add(PARAMS_CMD[i])
        if frm_new is not None:
            frm_new.grid(row=len(self.frames), column=0, padx=5, pady=5, sticky="ew", columnspan=1)
            self.frames.append(frm_new)
    # ---------------------------------------------------------------------------------------------
    def lst_rmv(self, item):
        """
        Function: remove the entry that initiated the function.
        """
        for frm in self.frames:
            if frm is item:
                frm.destroy()
                self.frames.remove(frm)
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
            width = 148,
            height = 28,
            text = "Experiment Folder:"
        )
        self.lbl_pth.grid(row=0, column=0, padx=(10,0), pady=5, sticky="nsew")
        self.ent_pth = customtkinter.CTkEntry(
            master = self,
            height = 28,
            textvariable = tkinter.StringVar(master=self, value=PARAMS_DFT)
        )
        self.ent_pth.grid(row=0, column=1, padx=(5,10), pady=5, sticky="ew", columnspan=5)
        # create appending control options
        self.lbl_typ = customtkinter.CTkLabel(
            master = self,
            width = 148,
            text = "New Command Type: "
        )
        self.lbl_typ.grid(row=1, column=0, padx=(12,0), pady=5, sticky="nesw")
        self.inp_typ = customtkinter.CTkComboBox(master=self, values=PARAMS_CMD)
        self.inp_typ.grid(row=1, column=1, padx=5, pady=5, sticky="nesw")
        self.btn_add = customtkinter.CTkButton(
            master = self,
            text = "Append to List",
            command = lambda: master.lst_add(inst=self.inp_typ.get())
        )
        self.btn_add.grid(row=1, column=2, padx=5, pady=5, sticky="nesw")
        self.lbl_mid = customtkinter.CTkLabel(
            master = self,
            text = "or Import:",
            width = 55
        )
        self.lbl_mid.grid(row=1, column=3, padx=(11,11), pady=5, sticky="nesw")
        self.btn_im1 = customtkinter.CTkButton(
            master = self,
            text = "From Folder",
            command = lambda: self.imp_fdr(self.ent_pth.get())
        )
        self.btn_im1.grid(row=1, column=4, padx=(5,10), pady=5, sticky="nesw")
        self.btn_im2 = customtkinter.CTkButton(master=self, text="From Log File")
        self.btn_im2.grid(row=1, column=5, padx=(0,10), pady=5, sticky="nesw")
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on call ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def imp_fdr(self, dirc):
        """
        Function: import scan scheme from experiment folders.
        """
        loc = pandas.read_csv(os.path.join(dirc, "_coordinates.csv")).values.tolist()
        img = []
        with os.scandir(dirc) as entries:
            for entry in entries:
                if entry.is_dir():
                    for file in os.listdir(entry):
                        if file[-4:] == ".png":
                            img.append(get_dtl(os.path.join(entry, file)))
        for i, image in enumerate(img):
            self.master.lst_add(PARAMS_CMD[0], [loc[i][1], loc[i][2], loc[i][3]], image, PARAMS_LSR[0])
            self.master.lst_add(PARAMS_CMD[1])


class Lsr(customtkinter.CTkFrame):
    """
    Class: ctk frame for individual laser instrument command.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, master, item, cord=None, mask=None, uses=None, **kwargs):
        super().__init__(master, **kwargs)
        # ------------------------------ initialize frame GUI layout ------------------------------
        self.configure(fg_color="grey23")
        # initialize marking label
        self.lbl_itr = customtkinter.CTkLabel(master=self, width=28, text=f"{item}")
        self.lbl_itr.grid(row=0, column=0, padx=(5,0), pady=5)
        self.lbl_typ = customtkinter.CTkLabel(master=self, width=65, text="Laser")
        self.lbl_typ.grid(row=0, column=1, padx=(0,5), pady=5)
        # create input entry boxes
        self.inp_ctx = customtkinter.CTkEntry(master=self, width=95)
        self.inp_ctx.grid(row=0, column=2, padx=5, pady=5)
        self.inp_cty = customtkinter.CTkEntry(master=self, width=95)
        self.inp_cty.grid(row=0, column=3, padx=5, pady=5)
        self.inp_ctz = customtkinter.CTkEntry(master=self, width=95)
        self.inp_ctz.grid(row=0, column=4, padx=5, pady=5)
        if cord is not None:
            self.inp_ctx.configure(textvariable=tkinter.StringVar(master=self, value=cord[0]))
            self.inp_cty.configure(textvariable=tkinter.StringVar(master=self, value=cord[1]))
            self.inp_ctz.configure(textvariable=tkinter.StringVar(master=self, value=cord[2]))
        else:
            self.inp_ctx.configure(placeholder_text="Center X")
            self.inp_cty.configure(placeholder_text="Center Y")
            self.inp_ctz.configure(placeholder_text="Center Z")
        self.inp_dms = customtkinter.CTkEntry(
            master = self,
            width = 150
        )
        self.inp_dms.grid(row=0, column=5, padx=5, pady=5)
        if mask is not None:
            self.inp_dms.configure(textvariable=tkinter.StringVar(master=self, value=mask))
        else:
            self.inp_dms.configure(placeholder_text="Relative Path")
        self.btn_img = customtkinter.CTkButton(
            master = self,
            width = 28,
            text = "...",
            command = print("open image editing")
        )
        self.btn_img.grid(row=0, column=6, padx=5, pady=5)
        self.inp_drp = customtkinter.CTkOptionMenu(master=self, width=95, values=PARAMS_LSR)
        if uses is not None:
            self.inp_drp.set(uses)
        self.inp_drp.grid(row=0, column=7, padx=5, pady=5)
        self.frm_opt = Opt(master=self)
        self.frm_opt.grid(row=0, column=8, padx=0, pady=0)


class Flu(customtkinter.CTkFrame):
    """
    Class: ctk frame for individual fluid instrument command.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, master, item, port=None, rate=None, volm=None, **kwargs):
        super().__init__(master, **kwargs)
        # ------------------------------ initialize frame GUI layout ------------------------------
        self.configure(fg_color="grey23")
        # initialize marking label
        self.lbl_itr = customtkinter.CTkLabel(master=self, width=28, text=f"{item}")
        self.lbl_itr.grid(row=0, column=0, padx=(5,0), pady=5)
        self.lbl_typ = customtkinter.CTkLabel(master=self, width=65, text="Fluidic")
        self.lbl_typ.grid(row=0, column=1, padx=(0,5), pady=5)
        # create input entry boxes
        self.inp_prt = customtkinter.CTkEntry(master=self, width=95)
        self.inp_prt.grid(row=0, column=2, padx=5, pady=5)
        if port is not None:
            self.inp_prt.configure(textvariable=tkinter.StringVar(master=self, value=port))
        else:
            self.inp_prt.configure(placeholder_text="Flow Port")
        self.inp_flw = customtkinter.CTkEntry(master=self, width=95)
        self.inp_flw.grid(row=0, column=3, padx=5, pady=5)
        if rate is not None:
            self.inp_flw.configure(textvariable=tkinter.StringVar(master=self, value=rate))
        else:
            self.inp_flw.configure(placeholder_text="Rate (uL/min)")
        self.inp_vol = customtkinter.CTkEntry(master=self, width=95)
        self.inp_vol.grid(row=0, column=4, padx=5, pady=5)
        if volm is not None:
            self.inp_vol.configure(textvariable=tkinter.StringVar(master=self, value=volm))
        else:
            self.inp_vol.configure(placeholder_text="Volume (uL)")
        self.frm_opt = Opt(master=self)
        self.frm_opt.grid(row=0, column=5, padx=(305,0), pady=0)


class Pse(customtkinter.CTkFrame):
    """
    Class: ctk frame for individual pause instrument command.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, master, item, time=None, **kwargs):
        super().__init__(master, **kwargs)
        # ------------------------------ initialize frame GUI layout ------------------------------
        self.configure(fg_color="grey23")
        # initialize marking label
        self.lbl_itr = customtkinter.CTkLabel(master=self, width=28, text=f"{item}")
        self.lbl_itr.grid(row=0, column=0, padx=(5,0), pady=5)
        self.lbl_typ = customtkinter.CTkLabel(master=self, width=65, text="Wait")
        self.lbl_typ.grid(row=0, column=1, padx=(0,5), pady=5)
        # create input entry boxes
        self.inp_tim = customtkinter.CTkEntry(master=self, width=95)
        self.inp_tim.grid(row=0, column=2, padx=5, pady=5)
        if time is not None:
            self.inp_tim.configure(textvariable=tkinter.StringVar(master=self, value=time))
        else:
            self.inp_tim.configure(placeholder_text="Time (ms)")
        self.frm_opt = Opt(master=self)
        self.frm_opt.grid(row=0, column=3, padx=(517,0), pady=0)


class Opt(customtkinter.CTkFrame):
    """
    Class: ctk frame with extra option menu for command frames.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        # -------------------------------------- GUI setting --------------------------------------
        self.configure(fg_color="transparent")
        # create extra option menu
        self.btn_mup = customtkinter.CTkButton(
            master = self,
            width = 28,
            text = "▴",
            command = lambda: master.master.lst_swp(self.master, "up"),
            fg_color = "transparent",
            border_width = 1,
            hover_color = "gray32"
        )
        self.btn_mup.grid(row=0, column=8, padx=5, pady=5)
        self.btn_mdn = customtkinter.CTkButton(
            master = self,
            width = 28,
            text = "▾",
            command = lambda: master.master.lst_swp(self.master, "down"),
            fg_color = "transparent",
            border_width = 1,
            hover_color = "gray32"
        )
        self.btn_mdn.grid(row=0, column=9, padx=5, pady=5)
        self.btn_rmv = customtkinter.CTkButton(
            master = self,
            width = 28,
            text = "-",
            command = lambda: master.master.lst_rmv(self.master),
            fg_color = "transparent",
            border_width = 1,
            hover_color = "#B62B24"
        )
        self.btn_rmv.grid(row=0, column=10, padx=5, pady=5)


# ===================================== independent functions =====================================

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
