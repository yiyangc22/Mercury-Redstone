"""
Mercury 04: image stitching previews, project version 1.2 (with python 3.9).
"""

import os
import tkinter as tk
from datetime import date

import pandas as pd
import customtkinter
import matplotlib.pyplot as plt
from PIL import Image

from mercury_01 import pyplot_create_region, open_file_dialog
from mercury_02 import read_xycoordinates

WINDOW_TXT = "Mercury IV - Image Stitching Preview"
WINDOW_RES = "800x100"

PARAMS_DTP = os.path.join(os.path.expanduser("~"), "Desktop")
PARAMS_EXP = os.path.join(PARAMS_DTP, f"latest_{date.today()}")
PARAMS_MCI = "image_multichannel"
PARAMS_MSK = "image_mask"
PARAMS_LSR = "image_laser"
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
            text = "Overlay Laser Images",
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
        try:
            # clear previous plots
            plt.clf()
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
            preview_stitching(images, coords, 366, 366, 180, center_index=True)
            # show plot preview window
            plt.gca().set_aspect('equal')
            plt.gcf().set_figheight(10)
            plt.gcf().set_figwidth(10)
            plt.show()
        except (AttributeError, IndexError, FileNotFoundError) as e:
            print(f"Warning: error occured in function `app_cmc_mlt`: {e}.")
    # ---------------------------------------------------------------------------------------------
    def app_cmc_msk(self, show_preview = True):
        """
        Function: preview stitching for laser masks.
        """
        try:
            # clear previous plots
            plt.clf()
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
            preview_stitching(images, coords, 366, 366, 180, center_index=True)
            # show plot preview window
            if show_preview:
                plt.gca().set_aspect('equal')
                plt.gcf().set_figheight(10)
                plt.gcf().set_figwidth(10)
                plt.show()
        except (AttributeError, IndexError, FileNotFoundError) as e:
            print(f"Warning: error occured in function `app_cmc_msk`: {e}.")
    # ---------------------------------------------------------------------------------------------
    def app_cmc_lsr(self):
        """
        Function: preview stitching for laser images.
        """
        try:
            # clear previous plots
            plt.clf()
            # show mask stitching result as background
            self.app_cmc_msk(show_preview=False)
            # acquire round number and image paths, return if error is encountered
            try:
                num_round = int(self.ent_rnd.get())
                file_endswith = '.tif'
                file_location = os.path.join(self.frm_ctl.ent_pth.get(), PARAMS_LSR)
                list_location = os.path.join(self.frm_ctl.ent_pth.get(), PARAMS_SCT)
                center = pd.read_csv(
                    list_location, keep_default_na = False, usecols=[1,2,4,5,6,7]).values.tolist()
                coords = []
                images = []
                for file in os.listdir(file_location):
                    if file[-len(file_endswith):] == file_endswith and file[0:5] != "Round":
                        file_prefix_num = int(file[0:4]) - 1000
                        file_affix_num = int(file[5:9]) - 1000
                        if file_prefix_num == num_round:
                            coords.append(center[file_affix_num])
                            images.append(os.path.join(file_location, file))
                if len(images) == 0:
                    print(f"Warning: found no laser images with matching round number {num_round}.")
                    return
            except (ValueError, TypeError) as e:
                print(f"Warning: error accessing image paths/coordinates due to user input: {e}.")
                return
            # check list lengths, initiate preview
            if len(images) != len(coords):
                print(f"Warning: found {len(images)} images, {len(coords)} coordinate pairs.")
                return
            preview_stitching(images, coords, 366, 366, 180, export_result=True)
            # show plot preview window
            plt.gca().set_aspect('equal')
            plt.gcf().set_figheight(10)
            plt.gcf().set_figwidth(10)
            plt.show()
        except (AttributeError, IndexError, FileNotFoundError) as e:
            print(f"Warning: error occured in function `app_cmc_lsr`: {e}.")
    # ---------------------------------------------------------------------------------------------
    def on_closing(self):
        """
        Function: enforce quit manually before closing.
        """
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

def preview_stitching(
        images: list,
        coords: list,
        width,
        height,
        rotation = 0,
        center_index = False,
        export_result = False,
        flip_top_bottom = False,
        flip_left_right = False
    ):
    """
    Function: construct pyplot preview for listed images and coordinates.
    """
    try:
        # determine round number
        round_num = int(os.path.basename(images[0])[0:4]) - 1000
        img_name = ""
        # create a new image to save stitched laser images
        if export_result:
            map_fld = os.path.join(os.path.dirname(os.path.dirname(images[0])), PARAMS_MAP)
            mask = Image.open(os.path.join(map_fld, f"Round {round_num}.png"))
            img = Image.new('I;16', mask.size, 'black')
            img_name = os.path.join(map_fld, f"Round {round_num}.tif")
        # initialize pyplot regions
        for i, coord in enumerate(coords):
            pyplot_create_region(
                coord[0],
                coord[1],
                width,
                height,
                i = i if center_index else os.path.basename(images[i]),
                j = images[i],
                a = 0.75,
                g = 1,
                r = rotation,
                d = flip_top_bottom,
                b = flip_left_right,
                f = 'center',
                v = 'center',
                t = 45
            )
            if export_result:
                # area_num = int(os.path.basename(images[i])[5:9]) - 1000
                tmp = Image.open(images[i]).resize([732, 732])
                tmp = tmp.crop((66, 66, 732-66, 732-66)).rotate(180)
                nesw = []
                for j in range(2, 6):
                    nesw.append(int(coords[i][j]))
                img.paste(tmp.resize([600, 600]), nesw)
                # if needed, save stitched image as a new file
                img.save(img_name)
    except (AttributeError, IndexError, FileNotFoundError) as e:
        print(f"Warning: error occured during stitching preview: {e}")


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
        app.protocol("WM_DELETE_WINDOW", app.on_closing)
        app.mainloop()
    except AttributeError:
        return None
