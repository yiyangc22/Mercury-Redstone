"""
Mercury 02: laser scheme constructor, project version 1.25 (with python 3.9).
"""

import os
import math
import threading
import traceback
import tkinter as tk
from itertools import combinations

import customtkinter
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image #, ImageOps
from matplotlib.collections import LineCollection

from mercury_00 import load_mask_preset
from mercury_01 import PARAMS_RES as MRES
from mercury_01 import pyplot_create_region, open_file_dialog, ctk_entry_warning

from params import PARAMS_DTP
# from params import PARAMS_EXP
from params import PARAMS_MCI
from params import PARAMS_MSK
# from params import PARAMS_LSR
from params import PARAMS_MAP
from params import PARAMS_PLN
from params import PARAMS_CRD
from params import PARAMS_GLB
from params import PARAMS_SCT
from params import PARAMS_BIT
# from params import PARAMS_TMP
from params import PARAMS_VER

# ctk window title
WINDOW_TXT = "Mercury II - Laser Scheme Constructor"
# default multichannel image size
PRES = 2304
# ctk frame parameters
PARAMS_TB1 = [
    {"width": None, "txt": "Submask Size (um)",      "val": 30,   "padx": (10,0),  "type": int},
    {"width": None, "txt": "Min Pixel Count",        "val": 5,    "padx": (10,0),  "type": int},
    {"width": None, "txt": "Max Concatenations",     "val": 5,    "padx": (10,0),  "type": int},
    {"width": None, "txt": "Multichannel Size (px)", "val": PRES, "padx": (10,0),  "type": int},
    {"width": None, "txt": "Mask Image Size (px)",   "val": MRES, "padx": (10,10), "type": int},
]
PARAMS_TB2 = [
    {"width": None, "txt": "Max Concatenations",     "val": 5,    "padx": (10,0),  "type": int},
    {"width": None, "txt": "Multichannel Size (px)", "val": PRES, "padx": (10,0),  "type": int},
    {"width": None, "txt": "Mask Image Size (px)",   "val": MRES, "padx": (10,10), "type": int},
]
# default mask image/text trail
PARAMS_TRL = ""
# default mask calibration preset file
PARAMS_MCP = os.path.join(os.path.dirname(os.path.realpath(__file__)), "default_calibration.yaml")
# default global multichannel file name (tif)
PARAMS_GMI = "image_multi_global.tif"


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
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.thread:threading.Thread = None
        self.params:list = None
        self.pth_folder:str = None
        self.tpl_preset:str = None
        self.pop_up:PopUpWindow = None
        self.laser_dimension = None
        self.cell_count = None
        self.txt_log = PARAMS_VER
        # -------------------------------------- GUI setting --------------------------------------
        # prompt user for experiment folder path
        self.frm_ctl = FileInput(master=self)
        self.frm_ctl.grid(row=0, column=0, padx=10, pady=(10,5), sticky="nesw", columnspan=1)
        # prompt user for laser mask calibration preset
        self.frm_mcp = FileInput(
            master=self,
            str_name="Calibration Preset:",
            str_textvar=PARAMS_MCP,
            is_folder=False,
            init_dir=os.path.dirname(os.path.realpath(__file__))
        )
        self.frm_mcp.grid(row=1, column=0, padx=10, pady=(0,5), sticky="nesw", columnspan=1)
        # create ctk frames for grid-based export schemes
        self.grid_input = InputRow(master=self, params=PARAMS_TB1)
        self.grid_input.grid(row=2, column=0, padx=10, pady=(5,0), columnspan=1)
        self.grid_export = customtkinter.CTkButton(
            master=self, text="Use Grid-based Submasking (.png)", command=self.export_grid_submask
        )
        self.grid_export.grid(row=3, column=0, padx=10, pady=5, sticky="nesw", columnspan=1)
        # create ctk frames for cell-based export schemes
        self.cell_input = InputRow(master=self, params=PARAMS_TB2)
        self.cell_input.grid(row=4, column=0, padx=10, pady=(5,0), sticky="nesw", columnspan=1)
        self.cell_export = customtkinter.CTkButton(
            master=self, text="Use Cell-based Submasking (.npz)", command=self.export_cell_submask
        )
        self.cell_export.grid(row=5, column=0, padx=10, pady=(5,10), sticky="nesw", columnspan=1)
        # create label to display information on the bottom of the frame
        self.lbl_inf = customtkinter.CTkLabel(
            master=self, font=customtkinter.CTkFont(size=10), width=610
        )
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on call ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def on_closing(self):
        """
        Function: enforce quit manually before closing.
        """
        self.quit()
    # ---------------------------------------------------------------------------------------------
    def export_grid_submask(self):
        """
        Function: commence grid submask export in a background thread.
        """
        # read experiment folder, check if it's a valid folder path
        result, successful = self.frm_ctl.get_entry(check_for_folder=True)
        if not successful:
            self.lbl_inf.configure(text=result)
            self.lbl_inf.grid(row=6, column=0, padx=10, pady=(0,10), sticky="nesw", columnspan=1)
            return
        # if successful, update app class parameters for thread functions, clear information label
        self.pth_folder = result
        self.lbl_inf.grid_forget()
        # read mask calibration preset, check if it's a valid preset
        result, successful = self.frm_mcp.get_entry(check_for_folder=False)
        if not successful:
            self.lbl_inf.configure(text=result)
            self.lbl_inf.grid(row=6, column=0, padx=10, pady=(0,10), sticky="nesw", columnspan=1)
            return
        # if successful, check if mask preset is valid, then update parameter and clear info label
        tpl = load_mask_preset(result, scaling_factor=1)
        if tpl is False:
            self.lbl_inf.configure(
                text=f"Warning: cannot read {result} as mask calibration preset"
            )
            self.lbl_inf.grid(row=6, column=0, padx=10, pady=(0,10), sticky="nesw", columnspan=1)
            return
        self.tpl_preset = tpl
        self.lbl_inf.grid_forget()
        # read inputs, show error if type conversion failed
        result, successful = self.grid_input.get_entry()
        if not successful:
            self.lbl_inf.configure(text=result)
            self.lbl_inf.grid(row=6, column=0, padx=10, pady=(0,10), sticky="nesw", columnspan=1)
            return
        # if successful, update app class parameters for thread functions, clear information label
        self.params = result
        self.lbl_inf.grid_forget()
        # initialize a toplevel window (if one already exists, focus it into view)
        if self.pop_up is None or not self.pop_up.winfo_exists():
            # open a separate top level window
            self.pop_up = PopUpWindow(
                self,
                title="Progress",
                label_text="Initializing ...",
                label_wrap=390,
                geometry="400x120"
            )
        else:
            # focus on the top level window if it exist
            self.pop_up.focus()
        self.pop_up.after(10, self.pop_up.lift)
        # run export command on new thread, log changes
        self.txt_log += "\nexport type: grid"
        self.thread = threading.Thread(target=self.thread_grid_submask, daemon=True)
        self.thread.start()
    # ---------------------------------------------------------------------------------------------
    def thread_grid_submask(self):
        """
        Function: run grid submask construction in a separate thread.
        """
        ###########################################################################################
        # STEP 1: CREATE GLOBAL MASK
        self.txt_log += "\ncreate global mask:"
        try:
            # create cleave map folder if it doesn't exist
            if not os.path.exists(os.path.join(self.pth_folder, PARAMS_MAP)):
                os.mkdir(os.path.join(self.pth_folder, PARAMS_MAP))
            # get masks from folder, sort by name, and require image to end with a specific trail
            image_files = sorted([f for f in os.listdir(
                os.path.join(self.pth_folder, PARAMS_MSK)
            ) if f.endswith(PARAMS_TRL+".png")])
            if os.path.exists(os.path.join(self.pth_folder, PARAMS_MCI)):
                image_multi = sorted([f for f in os.listdir(
                    os.path.join(self.pth_folder, PARAMS_MCI)
                ) if f.endswith(PARAMS_TRL+".tif")])
            else:
                image_multi = []
            # get multichannel coordinates (best to use planned coordinates for simplicity)
            coord_multi = read_xycoordinates(os.path.join(self.pth_folder, PARAMS_PLN))
            # if number of images does not match number of coordinates, raise error
            if len(image_files) != len(coord_multi):
                message = f"found {len(image_files)} masks, {len(coord_multi)} coordinates"
                raise IndexError(message)
            if len(image_multi) != 0 and len(image_multi) != len(coord_multi):
                message = f"found {len(image_multi)} images, {len(coord_multi)} coordinates"
                raise IndexError(message)
            # get multichannel and mask px size from stored variable
            int_smsize = self.params[0]
            self.txt_log += f"\n\tsubmask size: {int_smsize}"
            int_min_px = self.params[1]
            self.txt_log += f"\n\tsubmask px threshold: {int_min_px}"
            int_concat = self.params[2]
            self.txt_log += f"\n\tconcatenations: {int_concat}"
            int_multpx = self.params[3]
            self.txt_log += f"\n\tmultichannel image size: {int_multpx}"
            int_maskpx = self.params[4]
            self.txt_log += f"\n\tmask image size: {int_maskpx}"
            # calculate how large is the scan areas (in um)
            _r, _v, _h, _x, _y, width, height = self.tpl_preset
            laser_w_um = round((width/int_multpx)*int_maskpx)
            laser_h_um = round((height/int_multpx)*int_maskpx)
            self.txt_log += f"\n\tlaser scan size: ({laser_w_um},{laser_h_um})"
            # find min/max x and y values from multichannel image coordinates
            min_x_um = min(x for x, y in coord_multi)
            max_x_um = max(x for x, y in coord_multi)
            min_y_um = min(y for x, y in coord_multi)
            max_y_um = max(y for x, y in coord_multi)
            self.txt_log += f"\n\tmin/max multichannel x: ({min_x_um},{max_x_um})"
            self.txt_log += f"\n\tmin/max multichannel y: ({min_y_um},{max_y_um})"
            # use min/max x and y values to determine x and y tissue range
            range_x_um = abs(max_x_um - min_x_um) + int_maskpx
            range_y_um = abs(max_y_um - min_y_um) + int_maskpx
            # find submasked area size, will be divided into submasks (larger than tissue area)
            submask_area_w = math.ceil(range_x_um / int_smsize) * int_smsize
            submask_area_h = math.ceil(range_y_um / int_smsize) * int_smsize
            self.txt_log += f"\n\tsubmasking area: ({submask_area_w},{submask_area_h})"
            # find global mask dimensions, will include all submasks (larger than submask area)
            global_mask_w = math.ceil(submask_area_w / laser_w_um) * laser_w_um
            global_mask_h = math.ceil(submask_area_h / laser_h_um) * laser_h_um
            self.txt_log += f"\n\tglobal mask size: ({global_mask_w},{global_mask_h})"
            # create empty image for global mask
            global_mask = Image.new(
                'P',
                (global_mask_w, global_mask_h),
                color = (255,255,255)
            )
            if len(image_multi) != 0:
                global_multi = Image.new(
                    'I;16',
                    (global_mask_w, global_mask_h)
                )
            # find starting xy coordinates (top-left center) for pasting masks onto global mask
            int_start_x_px = round((global_mask_w - range_x_um)/2)
            int_start_y_px = round((global_mask_h - range_y_um)/2)
            # stitch global mask using multichannel coordinates
            for i, xy_pair in enumerate(coord_multi):
                # first, find the corresponding image
                img_path = os.path.join(os.path.join(self.pth_folder, PARAMS_MSK), image_files[i])
                img = invert_p_mode_image(Image.open(img_path))
                if len(image_multi) != 0:
                    mlt_path=os.path.join(os.path.join(self.pth_folder,PARAMS_MCI),image_multi[i])
                    mlt = Image.open(mlt_path).resize(img.size)
                    mlt = mlt.transpose(method=Image.Transpose.FLIP_LEFT_RIGHT)
                    mlt = mlt.transpose(method=Image.Transpose.FLIP_TOP_BOTTOM)
                # adjust for the inversion effect from the microscope before pasting
                img = img.transpose(method=Image.Transpose.FLIP_LEFT_RIGHT)
                img = img.transpose(method=Image.Transpose.FLIP_TOP_BOTTOM)
                # then, find pixel coordinates for the mask to paste onto
                x_px = round(int_start_x_px + (xy_pair[0] - min_x_um))
                   # = starting x + (recorded multichannel x - min recorded multichannel x)
                y_px = round(int_start_y_px + (max_y_um - xy_pair[1]))
                   # = starting y + (max recorded multichannel y - recorded multichannel y)
                # paste designated mask image onto the global mask
                global_mask.paste(img, (x_px, y_px))
                if len(image_multi) != 0:
                    global_multi.paste(mlt, (x_px, y_px))
                # update toplevel window text
                self.pop_up.set_text(
                    text=f"Creating global mask ...\n(mask {i}/{len(coord_multi)})"
                )
                self.pop_up.set_progress(i/len(coord_multi))
            # save output image
            global_mask.convert('L')
            global_mask.save(os.path.join(self.pth_folder, PARAMS_GLB))
            if len(image_multi) != 0:
                global_multi.save(os.path.join(self.pth_folder, PARAMS_GMI))
        except (ValueError, IndexError, TypeError, RuntimeError, FileNotFoundError) as e:
            traceback.print_exc()
            self.pop_up.set_text(
                text=f"Cannot stitch masks - {e}\n** Restart program to try again. **"
            )
            self.txt_log += f"\n{e}"
            with open(
                os.path.join(self.pth_folder, "mercury_02_log.txt"), 'w', encoding="utf-8"
            ) as file:
                file.write(self.txt_log)
            return
        self.txt_log += "\ndone"
        ###########################################################################################
        # STEP 2: SUBMASKING
        self.txt_log += "\ncreate submask:"
        try:
            # create submask list
            submasks = []
            # find submasking grid vertex coordinates (top-left, nw)
            submask_vertex_px = [
                round((global_mask_w - submask_area_w)/2),
                round((global_mask_h - submask_area_h)/2)
            ]
            submask_vertex_um = [
                round(min_x_um - int_maskpx/2 - (submask_area_w - range_x_um)/2 + int_smsize/2),
                round(max_y_um + int_maskpx/2 + (submask_area_h - range_y_um)/2 - int_smsize/2)
            ]
            # loop through all possible submasking areas
            num_rows = int(submask_area_h/int_smsize)
            for row in range(num_rows):
                for col in range(int(submask_area_w/int_smsize)):
                    # crop submask section
                    this_locus = [
                        submask_vertex_px[0] + col*int_smsize,
                        submask_vertex_px[1] + row*int_smsize,
                        submask_vertex_px[0] + col*int_smsize + int_smsize,
                        submask_vertex_px[1] + row*int_smsize + int_smsize
                    ]
                    this_submask = global_mask.crop(this_locus)
                    # calculate the number of non-white pixels in submask section
                    if count_non_white_pixel(this_submask) > int_min_px:
                        this_locus.insert(0, submask_vertex_um[1] - row*int_smsize)
                        this_locus.insert(0, submask_vertex_um[0] + col*int_smsize)
                        submasks.append(this_locus)
                # update toplevel window text
                self.pop_up.set_text(
                    text=f"Mapping submasks ...\n(row {row}/{num_rows})"
                )
                self.pop_up.set_progress(row/num_rows)
            self.txt_log += f"\n\tnumber of submasks: {len(submasks)}"
        except (ValueError, IndexError, TypeError, RuntimeError, FileNotFoundError) as e:
            traceback.print_exc()
            self.pop_up.set_text(
                text=f"Cannot apply submasking - {e}\n** Restart program to try again. **"
            )
            self.txt_log += f"\n{e}"
            with open(
                os.path.join(self.pth_folder, "mercury_02_log.txt"), 'w', encoding="utf-8"
            ) as file:
                file.write(self.txt_log)
            return
        self.txt_log += "\ndone"
        ###########################################################################################
        # STEP 3: CALCULATE SCAN CENTER COORDINATES
        self.txt_log += "\ncreate scan scheme:"
        try:
            # calculate xy center coordinates for first laser scan rectangle
            int_start_x_um = min_x_um-int_maskpx/2-(global_mask_w-range_x_um)/2+laser_w_um/2
            int_start_y_um = max_y_um+int_maskpx/2+(global_mask_h-range_y_um)/2-laser_h_um/2
            # read multichannel z values stored from previous step (mercury 01)
            coord_multi_z = read_zcoordinates(os.path.join(self.pth_folder, PARAMS_CRD))
            # loop through all laser scan rectangles, append xyz and wnes coordinates
            df = []
            for row in range(round(global_mask_h / laser_h_um)):
                for col in range(round(global_mask_w / laser_w_um)):
                    # calculate x, y, z, w, n, e, s coordinates for each scan rectangle
                    temp = [int_start_x_um + col*laser_w_um, int_start_y_um - row*laser_h_um]
                    temp.append(coord_multi_z[find_closest(coord_multi, temp)])
                    temp.extend([
                        col*laser_w_um,     # w
                        row*laser_h_um,     # n
                        (col+1)*laser_w_um, # e
                        (row+1)*laser_h_um  # s
                    ])
                    df.append(temp)
                # update toplevel window text
                self.pop_up.set_text(
                    text=f"Mapping scan areas ...\n(row {row}/{round(global_mask_h/laser_h_um)})"
                )
                self.pop_up.set_progress(row/(global_mask_h/laser_h_um))
            self.txt_log += f"\n\tscan scheme length: {len(df)}"
            df = pd.DataFrame(df, columns=['x','y','z','w','n','e','s'])
            df.to_csv(os.path.join(self.pth_folder, PARAMS_SCT), index=True)
        except (ValueError, IndexError, TypeError, RuntimeError, FileNotFoundError) as e:
            traceback.print_exc()
            self.pop_up.set_text(
                text=f"Cannot map scan centers - {e}\n** Restart program to try again. **"
            )
            self.txt_log += f"\n{e}"
            with open(
                os.path.join(self.pth_folder, "mercury_02_log.txt"), 'w', encoding="utf-8"
            ) as file:
                file.write(self.txt_log)
            return
        self.txt_log += "\ndone"
        ###########################################################################################
        # STEP 4: GENERATE BIT STRINGS
        self.txt_log += "\ncreate bit string:"
        try:
            bit_scheme, num_col = generate_digit_sequences(len(submasks), int_concat)
            self.txt_log += f"\n\tbit string length: {num_col}"
            # concatenate bit strings to submask coordinates
            for i, bit_string in enumerate(bit_scheme):
                submasks[i].append(np.nan)
                submasks[i].append(bit_string)
            # save submask coordinates and bit string as csv
            df = pd.DataFrame(submasks, columns=['x','y','w','n','e','s','index','bit'])
            df.to_csv(os.path.join(self.pth_folder, PARAMS_BIT), index=True)
        except (ValueError, IndexError, TypeError, RuntimeError, FileNotFoundError) as e:
            traceback.print_exc()
            self.pop_up.set_text(
                text=f"Cannot generate bit strings - {e}\n** Restart program to try again. **"
            )
            self.txt_log += f"\n{e}"
            with open(
                os.path.join(self.pth_folder, "mercury_02_log.txt"), 'w', encoding="utf-8"
            ) as file:
                file.write(self.txt_log)
            return
        self.txt_log += "\ndone"
        ###########################################################################################
        # STEP 5: GENERATE CLEAVE MAPS, EXIT
        self.txt_log += "\ncreate cleave maps:"
        try:
            # generate cleave maps for every position in a bit string
            global_arr = np.asarray(global_mask)
            regions = []
            # map submask coordinates
            for idx in submasks:
                x1, y1, x2, y2 = idx[2], idx[3], idx[4], idx[5]
                region_slice = (slice(y1, y2), slice(x1, x2))
                regions.append(region_slice)
            # loop through all rounds
            col = len(submasks[0][7])
            self.txt_log += "\n\tround(s) "
            for i in range(col):
                # set text and progress
                self.pop_up.set_text(
                    text=f"Creating cleave maps ...\n(round {i}/{col})"
                )
                self.pop_up.set_progress(i/col)
                # create new empty array as a representation of global image
                tmp_arr = np.full(
                    (global_mask_h, global_mask_w),
                    0,  # this sets the background color to white
                    dtype=global_arr.dtype
                )
                # use array to manipulate submasks
                for idx, region in zip(submasks, regions):
                    if idx[7][i] == 1:
                        ys, xs = region
                        tmp_arr[ys, xs] = global_arr[ys, xs]
                tmp_img = Image.fromarray(tmp_arr, mode=global_mask.mode)
                # specify palette, important because global mask is set in P (palette) mode
                tmp_img.putpalette(global_mask.getpalette())
                # save image and np array with the same more as original global mask
                tmp_img.save(
                    os.path.join(
                        self.pth_folder,
                        PARAMS_MAP,
                        f"Round {i}.png"
                    ),
                    format='PNG'
                )
                self.txt_log += f"{i}, "
            self.txt_log += "successfully processed"
        except (ValueError, IndexError, TypeError, RuntimeError, FileNotFoundError) as e:
            traceback.print_exc()
            self.pop_up.set_text(
                text=f"Cannot create cleave maps - {e}\n** Restart program to try again. **"
            )
            self.txt_log += f"\n{e}"
            with open(
                os.path.join(self.pth_folder, "mercury_02_log.txt"), 'w', encoding="utf-8"
            ) as file:
                file.write(self.txt_log)
            return
        # prompt user to exit
        self.laser_dimension = [laser_w_um, laser_h_um]
        self.txt_log += "\ndone"
        self.end_task()
    # ---------------------------------------------------------------------------------------------
    def export_cell_submask(self):
        """
        Function: commence cell-based submask export in a background thread.
        """
        # read experiment folder, check if it's a valid folder path
        result, successful = self.frm_ctl.get_entry(check_for_folder=True)
        if not successful:
            self.lbl_inf.configure(text=result)
            self.lbl_inf.grid(row=6, column=0, padx=10, pady=(0,10), sticky="nesw", columnspan=1)
            return
        # if successful, update app class parameters for thread functions, clear information label
        self.pth_folder = result
        self.lbl_inf.grid_forget()
        # read mask calibration preset, check if it's a valid preset
        result, successful = self.frm_mcp.get_entry(check_for_folder=False)
        if not successful:
            self.lbl_inf.configure(text=result)
            self.lbl_inf.grid(row=6, column=0, padx=10, pady=(0,10), sticky="nesw", columnspan=1)
            return
        # if successful, check if mask preset is valid, then update parameter and clear info label
        tpl = load_mask_preset(result, scaling_factor=1)
        if tpl is False:
            self.lbl_inf.configure(
                text=f"Warning: cannot read {result} as mask calibration preset"
            )
            self.lbl_inf.grid(row=6, column=0, padx=10, pady=(0,10), sticky="nesw", columnspan=1)
            return
        self.tpl_preset = tpl
        self.lbl_inf.grid_forget()
        # read inputs, show error if type conversion failed
        result, successful = self.cell_input.get_entry()
        if not successful:
            self.lbl_inf.configure(text=result)
            self.lbl_inf.grid(row=6, column=0, padx=10, pady=(0,10), sticky="nesw", columnspan=1)
            return
        # if successful, update app class parameters for thread functions, clear information label
        self.params = result
        self.lbl_inf.grid_forget()
        # initialize a toplevel window (if one already exists, focus it into view)
        if self.pop_up is None or not self.pop_up.winfo_exists():
            # open a separate top level window
            self.pop_up = PopUpWindow(
                self,
                title="Progress",
                label_text="Initializing ...",
                label_wrap=390,
                geometry="400x120"
            )
        else:
            # focus on the top level window if it exist
            self.pop_up.focus()
        self.pop_up.after(10, self.pop_up.lift)
        # run export command on new thread, log changes
        self.txt_log += "\nexport type: cell"
        self.thread = threading.Thread(target=self.thread_cell_submask, daemon=True)
        self.thread.start()
    # ---------------------------------------------------------------------------------------------
    def thread_cell_submask(self):
        """
        Function: run cell-based submask construction in a separate thread.
        """
        ###########################################################################################
        # STEP 1: CREATE GLOBAL MASK
        self.txt_log += "\ncreate global mask:"
        try:
            # update toplevel window text
            self.pop_up.set_text(
                text="Creating global mask ...\n(0/1)"
            )
            self.pop_up.set_progress(0)
            # create cleave map folder if it doesn't exist
            if not os.path.exists(os.path.join(self.pth_folder, PARAMS_MAP)):
                os.mkdir(os.path.join(self.pth_folder, PARAMS_MAP))
            # get masks from folder, sort by name, and require image to end with a specific trail
            image_files = sorted([f for f in os.listdir(
                os.path.join(self.pth_folder, PARAMS_MSK)
            ) if f.endswith(PARAMS_TRL+".png")])
            if os.path.exists(os.path.join(self.pth_folder, PARAMS_MCI)):
                image_multi = sorted([f for f in os.listdir(
                    os.path.join(self.pth_folder, PARAMS_MCI)
                ) if f.endswith(PARAMS_TRL+".tif")])
            else:
                image_multi = []
            array_files = sorted([f for f in os.listdir(
                os.path.join(self.pth_folder, PARAMS_MSK)
            ) if f.endswith(PARAMS_TRL+".npz")])
            # get multichannel coordinates (best to use planned coordinates for simplicity)
            coord_multi = read_xycoordinates(os.path.join(self.pth_folder, PARAMS_PLN))
            # if number of images does not match number of coordinates, raise error
            if len(image_files) != len(coord_multi):
                message = f"found {len(image_files)} images, {len(coord_multi)} coordinates"
                raise IndexError(message)
            if len(image_multi) != 0 and len(image_multi) != len(coord_multi):
                message = f"found {len(image_multi)} images, {len(coord_multi)} coordinates"
                raise IndexError(message)
            # get multichannel and mask px size from stored variable
            int_concat = self.params[0]
            self.txt_log += f"\n\tconcatenations: {int_concat}"
            int_multpx = self.params[1]
            self.txt_log += f"\n\tmultichannel image size: {int_multpx}"
            int_maskpx = self.params[2]
            self.txt_log += f"\n\tmask image size: {int_maskpx}"
            # calculate how large is the scan areas (in um)
            _r, _v, _h, x, y, width, height = self.tpl_preset
            laser_w_um = round((width/int_multpx)*int_maskpx)
            laser_h_um = round((height/int_multpx)*int_maskpx)
            self.txt_log += f"\n\tlaser scan size: ({laser_w_um},{laser_h_um})"
            # find min/max x and y values from multichannel image coordinates
            min_x_um = min(x for x, y in coord_multi)
            max_x_um = max(x for x, y in coord_multi)
            min_y_um = min(y for x, y in coord_multi)
            max_y_um = max(y for x, y in coord_multi)
            self.txt_log += f"\n\tmin/max multichannel x: ({min_x_um},{max_x_um})"
            self.txt_log += f"\n\tmin/max multichannel y: ({min_y_um},{max_y_um})"
            # use min/max x and y values to determine x and y tissue range
            range_x_um = abs(max_x_um - min_x_um) + int_maskpx
            range_y_um = abs(max_y_um - min_y_um) + int_maskpx
            # find global mask dimensions, will include all submasks (larger than submask area)
            global_mask_w = math.ceil(range_x_um / laser_w_um) * laser_w_um
            global_mask_h = math.ceil(range_y_um / laser_h_um) * laser_h_um
            self.txt_log += f"\n\tglobal mask size: ({global_mask_w},{global_mask_h})"
            # create empty image for global mask
            global_mask = Image.new(
                'P',
                (global_mask_w, global_mask_h),
                color = (255,255,255)
            )
            if len(image_multi) != 0:
                global_multi = Image.new(
                    'I;16',
                    (global_mask_w, global_mask_h)
                )
            # find starting xy coordinates (top-left center) for pasting masks onto global mask
            int_start_x_px = round((global_mask_w - range_x_um)/2)
            int_start_y_px = round((global_mask_h - range_y_um)/2)
            # stitch global mask using multichannel coordinates
            cell_count = []
            for i, xy_pair in enumerate(coord_multi):
                # first, find the corresponding image
                img_path = os.path.join(os.path.join(self.pth_folder, PARAMS_MSK), image_files[i])
                img = invert_p_mode_image(Image.open(img_path))
                if len(image_multi) != 0:
                    mlt_path=os.path.join(os.path.join(self.pth_folder,PARAMS_MCI),image_multi[i])
                    mlt = Image.open(mlt_path).resize(img.size)
                    mlt = mlt.transpose(method=Image.Transpose.FLIP_LEFT_RIGHT)
                    mlt = mlt.transpose(method=Image.Transpose.FLIP_TOP_BOTTOM)
                # adjust for the inversion effect from the microscope before pasting
                img = img.transpose(method=Image.Transpose.FLIP_LEFT_RIGHT)
                img = img.transpose(method=Image.Transpose.FLIP_TOP_BOTTOM)
                # then, find pixel coordinates for the mask to paste onto
                x_px = round(int_start_x_px + (xy_pair[0] - min_x_um))
                   # = starting x + (recorded multichannel x - min recorded multichannel x)
                y_px = round(int_start_y_px + (max_y_um - xy_pair[1]))
                   # = starting y + (max recorded multichannel y - recorded multichannel y)
                # paste designated mask image onto the global mask
                global_mask.paste(img, (x_px, y_px))
                if len(image_multi) != 0:
                    global_multi.paste(mlt, (x_px, y_px))
                # count how many cells are present in this mask
                npz_path = os.path.join(os.path.join(self.pth_folder, PARAMS_MSK), array_files[i])
                cell_count.append(int(np.load(npz_path, mmap_mode="r")["masks"].max()))
                # update toplevel window text
                self.pop_up.set_text(
                    text=f"Creating global mask ...\n(mask {i}/{len(coord_multi)})"
                )
                self.pop_up.set_progress(i/len(coord_multi))
            # save output image
            global_mask.convert('L')
            global_mask.save(os.path.join(self.pth_folder, PARAMS_GLB))
            if len(image_multi) != 0:
                global_multi.save(os.path.join(self.pth_folder, PARAMS_GMI))
        except (ValueError, IndexError, TypeError, RuntimeError, FileNotFoundError) as e:
            traceback.print_exc()
            self.pop_up.set_text(
                text=f"Cannot stitch masks - {e}\n** Restart program to try again. **"
            )
            self.txt_log += f"\n{e}"
            with open(
                os.path.join(self.pth_folder, "mercury_02_log.txt"), 'w', encoding="utf-8"
            ) as file:
                file.write(self.txt_log)
            return
        self.txt_log += "\ndone"
        ###########################################################################################
        # STEP 2: CALCULATE SCAN CENTER COORDINATES
        self.txt_log += "\ncreate scan scheme:"
        try:
            # calculate xy center coordinates for first laser scan rectangle
            int_start_x_um = min_x_um-int_maskpx/2-(global_mask_w-range_x_um)/2+laser_w_um/2
            int_start_y_um = max_y_um+int_maskpx/2+(global_mask_h-range_y_um)/2-laser_h_um/2
            # read multichannel z values stored from previous step (mercury 01)
            coord_multi_z = read_zcoordinates(os.path.join(self.pth_folder, PARAMS_CRD))
            # loop through all laser scan rectangles, append xyz and wnes coordinates
            df = []
            for row in range(round(global_mask_h / laser_h_um)):
                for col in range(round(global_mask_w / laser_w_um)):
                    # calculate x, y, z, w, n, e, s coordinates for each scan rectangle
                    temp = [int_start_x_um + col*laser_w_um, int_start_y_um - row*laser_h_um]
                    temp.append(coord_multi_z[find_closest(coord_multi, temp)])
                    temp.extend([
                        col*laser_w_um,     # w
                        row*laser_h_um,     # n
                        (col+1)*laser_w_um, # e
                        (row+1)*laser_h_um  # s
                    ])
                    df.append(temp)
                # update toplevel window text
                self.pop_up.set_text(
                    text=f"Mapping scan areas ...\n(row {row}/{round(global_mask_h/laser_h_um)})"
                )
                self.pop_up.set_progress(row/(global_mask_h/laser_h_um))
            self.txt_log += f"\n\tscan scheme length: {len(df)}"
            df = pd.DataFrame(df, columns=['x','y','z','w','n','e','s'])
            df.to_csv(os.path.join(self.pth_folder, PARAMS_SCT), index=True)
        except (ValueError, IndexError, TypeError, RuntimeError, FileNotFoundError) as e:
            traceback.print_exc()
            self.pop_up.set_text(
                text=f"Cannot map scan centers - {e}\n** Restart program to try again. **"
            )
            self.txt_log += f"\n{e}"
            with open(
                os.path.join(self.pth_folder, "mercury_02_log.txt"), 'w', encoding="utf-8"
            ) as file:
                file.write(self.txt_log)
            return
        self.txt_log += "\ndone"
        ###########################################################################################
        # STEP 3: GENERATE BIT STRINGS
        self.txt_log += "\nCreating bit string:"
        try:
            # update toplevel window text
            self.pop_up.set_text(
                text="Creating bit scheme ..."
            )
            self.pop_up.set_progress(0)
            bit_scheme, num_col = generate_digit_sequences(sum(cell_count), int_concat)
            self.txt_log += f"\n\tbit string length: {num_col}"
            self.txt_log += f"\n\ttotal cell number: {sum(cell_count)}"
            # concatenate bit strings
            cells = []
            for i, bit_string in enumerate(bit_scheme):
                temp = [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, i, bit_string]
                cells.append(temp)
            # save cell index and bit string as csv
            df = pd.DataFrame(cells, columns=['x','y','w','n','e','s','index','bit'])
            df.to_csv(os.path.join(self.pth_folder, PARAMS_BIT), index=True)
        except (ValueError, IndexError, TypeError, RuntimeError, FileNotFoundError) as e:
            traceback.print_exc()
            self.pop_up.set_text(
                text=f"Cannot generate bit strings - {e}\n** Restart program to try again. **"
            )
            self.txt_log += f"\n{e}"
            with open(
                os.path.join(self.pth_folder, "mercury_02_log.txt"), 'w', encoding="utf-8"
            ) as file:
                file.write(self.txt_log)
            return
        self.txt_log += "\ndone"
        ###########################################################################################
        # STEP 4: GENERATE CLEAVE MAPS, EXIT
        self.txt_log += "\ncreate cleave maps:"
        self.txt_log += "\n\tcell count for each round: "
        try:
            # save palette from original global mask
            global_mask_palette = global_mask.getpalette()
            # construct cleave maps for every fluidic round
            for i in range(num_col):
                # clear global mask as an empty background for constructing cleave maps
                global_mask = Image.new(
                    'P',
                    (global_mask_w, global_mask_h),
                    color = (255,255,255)
                )
                # reconstruct masks from arrays, saave global mask as cleave maps
                count = 0
                message = f"Creating cleave maps (round {i}/{num_col})"
                for j, xy_pair in enumerate(coord_multi):
                    # set text and progress
                    self.pop_up.set_text(
                        text=(message+f"\n(mask {j}/{len(coord_multi)})")
                    )
                    self.pop_up.set_progress(j/len(coord_multi))
                    # find and extract corresponding npz array
                    masks = np.load(
                        os.path.join(os.path.join(self.pth_folder, PARAMS_MSK), array_files[j]),
                        mmap_mode="r"
                    )["masks"]
                    # calculate selected cell indexes
                    selected_cells = []
                    for k in range(cell_count[j]):
                        if bit_scheme[count+k][i] == 1:
                            selected_cells.append(k+1)  # 0 is reserved for background
                    count += cell_count[j]
                    binary = np.isin(masks, selected_cells)
                    self.txt_log += f"{len(selected_cells)}, "
                    # use extractedd binary array and selected cell indexes to recreate mask
                    img = Image.fromarray(binary, mode='L')
                    # img = ImageOps.invert(img)
                    img = img.resize([int_maskpx, int_maskpx])
                    img.convert('P')
                    img.putpalette(global_mask_palette)
                    # adjust for the inversion effect from the microscope before pasting
                    img = img.transpose(method=Image.Transpose.FLIP_LEFT_RIGHT)
                    img = img.transpose(method=Image.Transpose.FLIP_TOP_BOTTOM)
                    # find pixel coordinates for the mask to paste onto
                    x_px = round(int_start_x_px + (xy_pair[0] - min_x_um))
                        # = starting x + (recorded multichannel x - min recorded multichannel x)
                    y_px = round(int_start_y_px + (max_y_um - xy_pair[1]))
                        # = starting y + (max recorded multichannel y - recorded multichannel y)
                    # paste designated mask image onto the global mask
                    global_mask.paste(img, (x_px, y_px))
                # convert cleave map to L mode, save
                global_mask.save(
                    os.path.join(
                        self.pth_folder,
                        PARAMS_MAP,
                        f"Round {i}.png"
                    ),
                    format='PNG'
                )
        except (ValueError, IndexError, TypeError, RuntimeError, FileNotFoundError) as e:
            traceback.print_exc()
            self.pop_up.set_text(
                text=f"Cannot create cleave maps - {e}\n** Restart program to try again. **"
            )
            self.txt_log += f"\n{e}"
            with open(
                os.path.join(self.pth_folder, "mercury_02_log.txt"), 'w', encoding="utf-8"
            ) as file:
                file.write(self.txt_log)
            return
        # prompt user to exit
        self.laser_dimension = [laser_w_um, laser_h_um]
        self.cell_count = cell_count
        self.txt_log += "\ndone"
        self.end_task()
    # ---------------------------------------------------------------------------------------------
    def end_task(self):
        """Function: finish export and prompt for user action."""
        # save logs
        self.txt_log += "\nall process finished with no error"
        with open(
            os.path.join(self.pth_folder, "mercury_02_log.txt"), 'w', encoding="utf-8"
        ) as file:
            file.write(self.txt_log)
        # prompt user to exit
        self.pop_up.set_text(text="Finished! You may exit the program now.")
        # show option to plot preview
        self.pop_up.pgb_prg.grid_forget()
        self.pop_up.btn_prv.grid(row=1, column=0, padx=10, pady=(0,10), sticky="nesw")


class FileInput(customtkinter.CTkFrame):
    """
    Class: ctk frame with string entry for folder/file path and button for prompting filedialogue.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(
            self,
            master,
            str_name=None,
            str_textvar=None,
            is_folder=True,
            init_dir=PARAMS_DTP,
            **kwargs
        ):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.use_folder = is_folder
        # -------------------------------------- GUI setting --------------------------------------
        # create file path entry and label
        self.lbl_pth = customtkinter.CTkLabel(
            master = self,
            width = 50,
            height = 28,
            text = "Experiment Folder:" if str_name is None else str_name
        )
        self.lbl_pth.grid(row=0, column=0, padx=(10,0), pady=5, columnspan=1)
        self.ent_pth = customtkinter.CTkEntry(
            master = self,
            width = 575,
            height = 28,
            textvariable = tk.StringVar(
                master=self, value=str_textvar
            )
        )
        self.ent_pth.grid(row=0, column=1, padx=5, pady=5, columnspan=1)
        self.btn_aof = customtkinter.CTkButton(
            master = self,
            width = 28,
            height = 28,
            text = "...",
            command = lambda: self.prompt_path(init_dir)
        )
        self.btn_aof.grid(row=0, column=2, padx=(0,10), pady=5, columnspan=1)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on call ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def prompt_path(self, init_dir):
        """
        Function: set ent_pth to filedialog output.
        """
        if self.use_folder:
            file_path = open_file_dialog(
                init_title = "Select a folder",
                init_dir = init_dir,
                init_types = False
            )
            if file_path != "":
                self.ent_pth.configure(textvariable=tk.StringVar(master=self, value=file_path))
        else:
            file_path = open_file_dialog(
                init_title = "Select a file",
                init_dir = init_dir
            )
            if file_path != "":
                self.ent_pth.configure(textvariable=tk.StringVar(master=self, value=file_path))
    # ---------------------------------------------------------------------------------------------
    def get_entry(self, check_for_folder:bool=False):
        """
        Function: get inputs from frame's entry widget, check if it's a valid folder/file path.
        """
        # if entry path is required to be a folder
        if check_for_folder:
            if os.path.isdir(self.ent_pth.get()):
                return (self.ent_pth.get(), True)
            # if above return is not triggered, show error and return error message
            ctk_entry_warning(self.ent_pth)
            return (f"Warning: cannot read \"{self.ent_pth.get()}\" as a valid folder path", False)
        # if entry path is required to be a file
        else:
            if os.path.exists(self.ent_pth.get()):
                return (self.ent_pth.get(), True)
            # if above return is not triggered, show error and return error message
            ctk_entry_warning(self.ent_pth)
            return (f"Warning: cannot read \"{self.ent_pth.get()}\" as a valid file path", False)


class InputRow(customtkinter.CTkFrame):
    """
    Class: ctk frame for adding a row of input boxes (with optional label and placeholder text).
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, master, params, **kwargs):
        super().__init__(master, **kwargs)
        # -------------------------------------- GUI setting --------------------------------------
        # define configuration parameters for submasking
        self.frames_list:list[InputCell] = []
        self.input_types:list[type] = []
        # create frames to control submasking parameters
        for i, config in enumerate(params):
            # set variable type
            self.input_types.append(config["type"])
            # set variable frame
            entry = InputCell(
                master = self,
                cell_width = config["width"],
                label = config["txt"],
                val = config["val"],
                fg_color = "transparent"
            )
            # set equal uniform group
            self.grid_columnconfigure(i, weight=1, uniform="group")
            # grid and append frame to frame list
            entry.grid(row=0, column=i, padx=config["padx"], pady=(5,10), sticky="nesw")
            self.frames_list.append(entry)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on call ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def get_entry(
            self,
            warn_color:str = "brown",
            warn_duration:int = 50
        ):
        """
        Function: get inputs, check input types, return error message and False if not compatable.
        """
        # loop through designated types, return warning message and show error if not compatable
        rtn = []
        for i, frame in enumerate(self.frames_list):
            # if there's an error, the input with type error will be highlighted briefly
            entry, successful = frame.get_entry(
                self.input_types[i], warn_color=warn_color, warn_duration=warn_duration
            )
            # if the type checking failed (type-checking returned None), break and return None
            if successful:
                rtn.append(entry)
            else:
                return (entry, False)
        # if no error occured, return input entries (with types converted) as a list
        return (rtn, True)


class InputCell(customtkinter.CTkFrame):
    """
    Class: ctk frame for an input cell (label + entry).
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, master, label, cell_width = None, val = None, placeholder = None, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        # -------------------------------------- GUI setting --------------------------------------
        self.label = customtkinter.CTkLabel(
            master = self,
            text = label,
            anchor = "w"
        )
        self.label.grid(row=0, column=0, padx=0, pady=0, sticky="nesw")
        if cell_width is not None:
            self.label.configure(width=cell_width)
        self.entry = customtkinter.CTkEntry(
            master = self
        )
        if cell_width is not None:
            self.entry.configure(width=cell_width)
        if val is not None:
            self.entry.configure(textvariable=tk.StringVar(master=self, value=val))
        elif placeholder is not None:
            self.entry.configure(placeholder_text=placeholder)
        self.entry.grid(row=1, column=0, padx=0, pady=0, sticky="nesw")
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on call ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def get_entry(
            self, check_type:type = str, warn_color:str = "brown", warn_duration:int = 50
        ):
        """
        Function: get input, check input's type, return error message and False if not compatable.
        """
        # try converting entry (str) to the input type, return True if successful
        try:
            return (check_type(self.entry.get()), True)
        # otherwise, print error message, show warning, and return error string
        except (ValueError, TypeError) as _:
            message = f"Warning: input \"{self.entry.get()}\" cannot be converted to {check_type}"
            ctk_entry_warning(self.entry, color=warn_color, duration=warn_duration)
            return (message, False)


class PopUpWindow(customtkinter.CTkToplevel):
    """
    Class: ctk top level window for checking commence progress.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, master, title, label_text, label_wrap=None, geometry=None, **kwargs):
        super().__init__(master, **kwargs)
        # ---------------------------------- application setting ----------------------------------
        self.title(title)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        if geometry is not None:
            self.geometry(geometry)
        # -------------------------------------- GUI setting --------------------------------------
        self.lbl_txt = customtkinter.CTkLabel(master=self, text=label_text)
        self.lbl_txt.grid(row=0, column=0, padx=10, pady=5, sticky="nesw")
        if label_wrap is not None:
            self.lbl_txt.configure(wraplength=label_wrap)
        self.pgb_prg = customtkinter.CTkProgressBar(master=self)
        self.pgb_prg.set(0)
        self.pgb_prg.grid(row=1, column=0, padx=10, pady=5, sticky="nesw")
        self.btn_prv = customtkinter.CTkButton(
            master=self,
            text="Preview Scan Scheme",
            command=self.preview_scheme
        )
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on call ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def set_text(self, text):
        """Function: update text label."""
        self.lbl_txt.configure(text=text)
    # ---------------------------------------------------------------------------------------------
    def set_progress(self, ratio):
        """Function: update progress bar."""
        self.pgb_prg.set(ratio)
    # ---------------------------------------------------------------------------------------------
    def on_closing(self):
        """Function: enforce quit manually before closing."""
        self.quit()
    # ---------------------------------------------------------------------------------------------
    def preview_scheme(self):
        """Function: preview laser scan scheme"""
        if self.master.laser_dimension is not None:
            if self.master.cell_count is None:
                preview_laser_grid(
                    exp_folder=self.master.pth_folder,
                    mask_size=self.master.params[4],
                    submask_size=self.master.params[0],
                    laser_w=self.master.laser_dimension[0],
                    laser_h=self.master.laser_dimension[1]
                )
            elif isinstance(self.master.cell_count, list):
                preview_laser_cell(
                    exp_folder=self.master.pth_folder,
                    mask_size=self.master.params[2],
                    laser_w=self.master.laser_dimension[0],
                    laser_h=self.master.laser_dimension[1],
                    num_cell=self.master.cell_count
                )
            else:
                print("Warning: cannot preview, cell count is not properly initialized")
        else:
            print("Warning: cannot preview, laser scan dimensions are not properly initialized")


# ===================================== independent functions =====================================

def generate_digit_sequences(num_fov:int, num_concat:int) -> tuple[list[int], int]:
    """
    ### Function: generate unique bit sequences for a given number of images.
    
    `num_fov` : Number of sequences to return.
    `num_concat` : Number of ones in each sequence.

    Returns *(bit_sequences, bit_string_length)*
    """
    # calculate minimum columns needed
    columns = num_concat
    while math.comb(columns, num_concat) < num_fov:
        columns += 1
    # generate combinations of positions where 1s should be placed
    # combinations() generates them in lexicographic order
    one_positions = combinations(range(columns), num_concat)
    sequences = []
    for positions in one_positions:
        if len(sequences) >= num_fov:
            break
        # Create sequence with 0s
        sequence = [0] * columns
        # Set 1s at specified positions
        for pos in positions:
            sequence[pos] = 1
        sequences.append(sequence)
    return (sequences, columns)


def read_xycoordinates(csv_file):
    """
    Function: read row 1 and 2 as x and y coordinates (ignore row 0)
    """
    # read .csv, save xy coordinates in list, and print
    csv = pd.read_csv(csv_file).values.tolist()
    coords = []
    for row in csv:
        # if needed, invert x (row[1]) or y (row[2]) axis here
        coords.append([row[1], row[2]])
    # create regions in matplotlib based on the coordinates
    return coords


def read_zcoordinates(csv_file):
    """
    Function: read row 3 as z coordinates (ignore row 0, 1, 2)
    """
    # read .csv, save xy coordinates in list, and print
    csv = pd.read_csv(csv_file).values.tolist()
    coords = []
    for row in csv:
        # if needed, invert x (row[1]) or y (row[2]) axis here
        coords.append(row[3])
    # create regions in matplotlib based on the coordinates
    return coords


def count_non_white_pixel(img: Image.Image) -> int:
    """
    Function: count the number of non-white pixels in an image
    """
    white_index = img.getpalette()[0:3]  # RGB for index 0
    for i in range(256):
        if img.getpalette()[i*3:i*3+3] == [255, 255, 255]:
            white_index = i
            break
    else:
        white_index = None  # No white found in palette
    pixels = img.getdata()
    if white_index is None:
        return len(pixels)
    return sum(1 for p in pixels if p != white_index)


def find_closest(coordinates, point):
    """
    Function: ind the index of the coordinate pair that is closest to the given point.
    
    Args:
        coordinates: List of coordinate pairs [[x1, y1], [x2, y2], ...]
        point: Target point [x, y]
    
    Returns:
        int: Index of the closest coordinate pair
    """
    target_x, target_y = point
    min_distance = float('inf')
    closest_index = 0
    # loop through all possible xy pairs
    for i, coord in enumerate(coordinates):
        x = coord[0]
        y = coord[1]
        # calculate euclidean distance
        distance = ((x - target_x) ** 2 + (y - target_y) ** 2) ** 0.5
        # keep the index of the closest coordinate pair
        if distance == 0:
            return i
        elif distance < min_distance:
            min_distance = distance
            closest_index = i
    return closest_index


def plot_rectangles(
    coords,
    width,
    height=None,
    *,
    ax=None,
    color='b',
    alpha=0.5,
    linewidth=1
):
    """
    Plot axis-aligned rectangles centered at given (x, y) coordinates
    using a single LineCollection for high performance.

    Parameters
    ----------
    coords : array-like, shape (N, 2)
        List/array of (x, y) center coordinates.
    width : float
        Rectangle width.
    height : float or None, optional
        Rectangle height. If None, height = width (square).
    ax : matplotlib.axes.Axes or None
        Axis to draw on. Defaults to current axis.
    color : str or tuple
        Line color.
    alpha : float
        Line transparency.
    linewidth : float
        Line width.

    Returns
    -------
    lc : matplotlib.collections.LineCollection
        The added LineCollection (useful for later modification).
    """
    if ax is None:
        ax = plt.gca()
    coords = np.asarray(coords)
    if coords.ndim != 2 or coords.shape[1] != 2:
        raise ValueError("coords must be an array-like of shape (N, 2)")
    if height is None:
        height = width
    half_w = width / 2
    half_h = height / 2
    # build rectangles: shape (N, 5, 2)
    rectangles = np.stack([
        np.column_stack([coords[:, 0] - half_w, coords[:, 1] + half_h]),
        np.column_stack([coords[:, 0] + half_w, coords[:, 1] + half_h]),
        np.column_stack([coords[:, 0] + half_w, coords[:, 1] - half_h]),
        np.column_stack([coords[:, 0] - half_w, coords[:, 1] - half_h]),
        np.column_stack([coords[:, 0] - half_w, coords[:, 1] + half_h]),
    ], axis=1)
    lc = LineCollection(
        rectangles,
        colors=color,
        alpha=alpha,
        linewidths=linewidth
    )
    ax.scatter(
        coords[:, 0],
        coords[:, 1],
        s=linewidth,
        c=color,
        alpha=alpha
    )
    ax.add_collection(lc)
    ax.autoscale()
    return lc


def preview_laser_grid(exp_folder, mask_size:int, submask_size:int, laser_w:int, laser_h:int):
    """
    Function: preview grid layouts of submasks and laser scan regions.
    """
    # clear previous plots
    plt.clf()
    # show mask stitching result as background
    try:
        file_endswith = '.png'
        file_location = os.path.join(exp_folder, PARAMS_MSK)
        images = []
        for file in os.listdir(file_location):
            if file[-len(file_endswith):] == file_endswith:
                images.append(os.path.join(file_location, file))
        # acquire multichannel coordinates
        file_location = os.path.join(exp_folder, PARAMS_PLN)    # planned or recorded coordinates
        coords = read_xycoordinates(file_location)
        # check list lengths, create elements on the plot
        if len(images) != len(coords):
            print(f"Warning: found {len(images)} masks, {len(coords)} coordinate pairs.")
            return
        for i, coord in enumerate(coords):
            pyplot_create_region(
                coord[0],
                coord[1],
                mask_size,
                mask_size,
                j = images[i],
                a = 0.25,
                r = 180,
                d = False,
                b = False,
                f = 'center',
                v = 'center',
                t = 45,
                c = 'g',
                e = 'g',
            )
    except (AttributeError, IndexError, FileNotFoundError) as e:
        print(f"Warning: error occured when plotting masks: {e}.")
    # show submasking result as midground
    try:
        file_location = os.path.join(exp_folder, PARAMS_BIT)
        coords_sm = pd.read_csv(file_location, usecols=['x','y']).values
        plot_rectangles(
            coords_sm,
            width=submask_size,
            color='g',
            alpha=1
        )
    except (AttributeError, IndexError, FileNotFoundError) as e:
        print(f"Warning: error occured when plotting submasks: {e}.")
    # show laser scan rectangles as foreground
    try:
        file_location = os.path.join(exp_folder, PARAMS_SCT)
        coords_ls = pd.read_csv(file_location, usecols=['x','y']).values
        plot_rectangles(
            coords_ls,
            width=laser_w,
            height=laser_h,
            color='r',
            alpha=1
        )
    except (AttributeError, IndexError, FileNotFoundError) as e:
        print(f"Warning: error occured when plotting laser scan areas: {e}.")
    # create textbox to display relevant parameters
    txt = f"Number of masks: {len(images)}\n"
    txt += f"Number of submasks: {len(coords_sm)}\n"
    txt += f"Number of laser scans: max {len(coords_ls)}\n\n"
    txt += f"Mask size: {mask_size} (um/px)\n"
    txt += f"Submask size: {submask_size} (um/px)\n"
    txt += f"Laser scan size: {laser_w}x{laser_h} (um/px)"
    plt.text(
        x = 1.05,
        y = 1,
        s = txt,
        transform = plt.gca().transAxes,
        fontsize = 10,
        verticalalignment='top',
        bbox = dict(facecolor='none', alpha=0.15)
    )
    # show constructed plot
    plt.gca().set_aspect('equal')
    plt.gcf().set_figwidth(15)
    plt.gcf().set_figheight(15)
    plt.tight_layout()
    plt.autoscale()
    plt.show()


def preview_laser_cell(exp_folder, mask_size:int, laser_w:int, laser_h:int, num_cell:list[int]):
    """
    Function: preview cell layouts of submasks and laser scan regions.
    """
    # clear previous plots
    plt.clf()
    # show mask stitching result as background
    try:
        file_endswith = '.png'
        file_location = os.path.join(exp_folder, PARAMS_MSK)
        images = []
        for file in os.listdir(file_location):
            if file[-len(file_endswith):] == file_endswith:
                images.append(os.path.join(file_location, file))
        # acquire multichannel coordinates
        file_location = os.path.join(exp_folder, PARAMS_PLN)    # planned or recorded coordinates
        coords = read_xycoordinates(file_location)
        # check list lengths, create elements on the plot
        if len(images) != len(coords):
            print(f"Warning: found {len(images)} masks, {len(coords)} coordinate pairs.")
            return
        for i, coord in enumerate(coords):
            pyplot_create_region(
                coord[0],
                coord[1],
                mask_size,
                mask_size,
                j = images[i],
                a = 1,
                r = 180,
                d = False,
                b = False,
                f = 'center',
                v = 'center',
                t = 45,
                c = 'g',
                e = 'g',
            )
    except (AttributeError, IndexError, FileNotFoundError) as e:
        print(f"Warning: error occured when plotting masks: {e}.")
    # show laser scan rectangles as foreground
    try:
        file_location = os.path.join(exp_folder, PARAMS_SCT)
        coords_ls = pd.read_csv(file_location, usecols=['x','y']).values
        plot_rectangles(
            coords_ls,
            width=laser_w,
            height=laser_h,
            color='r',
            alpha=1
        )
    except (AttributeError, IndexError, FileNotFoundError) as e:
        print(f"Warning: error occured when plotting laser scan areas: {e}.")
    # create textbox to display relevant parameters
    txt = f"Number of masks: {len(images)}\n"
    txt += f"Number of cells: {sum(num_cell)}\n"
    txt += f"Number of laser scans: max {len(coords_ls)}\n\n"
    txt += f"Mask size: {mask_size} (um/px)\n"
    txt += f"Laser scan size: {laser_w}x{laser_h} (um/px)"
    plt.text(
        x = 1.05,
        y = 1,
        s = txt,
        transform = plt.gca().transAxes,
        fontsize = 10,
        verticalalignment='top',
        bbox = dict(facecolor='none', alpha=0.15)
    )
    # show constructed plot
    plt.gca().set_aspect('equal')
    plt.gcf().set_figwidth(15)
    plt.gcf().set_figheight(15)
    plt.tight_layout()
    plt.autoscale()
    plt.show()


def invert_p_mode_image(image: Image.Image) -> Image.Image:
    """
    Invert a P mode (palette) PNG image.

    Converts to RGB before inverting to ensure pixel values are treated as
    actual colors rather than palette indices, then converts back to P mode
    using the original palette to avoid quantization loss.

    Args:
        image: A PIL Image in P mode.

    Returns:
        A PIL Image in P mode with inverted colors, using the original palette.

    Raises:
        ValueError: If the input image is not in P mode.
    """
    if image.mode != "P":
        raise ValueError(f"Expected P mode image, got {image.mode!r}")
    # invert the palette entries directly (lossless)
    palette = image.getpalette()  # list of [R, G, B, R, G, B, ...]
    inverted_palette = [255 - v for v in palette]
    output = image.copy()
    output.putpalette(inverted_palette)
    return output


# ========================================= main function =========================================

def mercury_02():
    """
    Main application loop of mercury 02, display constructed pyplot preview.
    """
    # set customtkinter appearance mode and color theme
    customtkinter.set_appearance_mode("dark")
    customtkinter.set_default_color_theme("blue")
    # enter main loop and return user inputs when ended
    try:
        app = App()
        app.resizable(False, False)
        app.protocol("WM_DELETE_WINDOW", app.on_closing)
        app.attributes("-topmost", True)
        app.after_idle(app.attributes, "-topmost", False)
        app.after(10, app.focus)
        app.mainloop()
    except (AttributeError, UserWarning, RuntimeError) as e:
        print(f"Warning: cannot initialize mainloop: {e}")
        return None
