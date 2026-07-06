"""
Mercury 03 (drop-modified): fluid scheme constructor, project version 1.24 (with python 3.9).

Difference from `mercury_03_copy.py`:
- Adds crash/termination resume support. If an experiment stops unexpectedly, rerun mercury_03
  on the same experiment folder and it will pick up where it left off. On rerun the image_laser
  folder is scanned for the last saved per-FOV laser image (its name encodes the round/area, same
  convention mercury_04 uses: file[0:4]-1000 = round, file[5:9]-1000 = area). That (round, area)
  boundary is written to `config_resume_point.csv`; during the LabVIEW run update_mask skips every
  area at or before it so the laser never re-fires on already-completed areas.
- Fixes a LabVIEW type error ("mismatching a real number with list"). The original "skip / not
  executed" return value was [[],[],[]] (a list of empty lists), which LabVIEW cannot coerce into
  the array-of-reals it expects for the (x, y, z) coordinate. It is replaced by an empty list []
  (an empty numeric array), which is type-safe and signals "no coordinate -> skip this area".
"""

import os
import tkinter as tk
from datetime import date

import pandas as pd
import customtkinter
from PIL import Image, ImageOps

from mercury_00 import load_mask_preset
from mercury_01 import open_file_dialog
from mercury_02 import count_non_white_pixel

Image.MAX_IMAGE_PIXELS = 450000000

WINDOW_TXT = "Mercury III - Fluid Scheme Constructor"
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
PARAMS_RSM = "config_resume_point.csv"

# value update_mask returns to tell LabVIEW "do not execute this area" (skip / not executed).
# it must be an array of real numbers, so an empty list [] (empty numeric array) is used rather
# than the original [[],[],[]] which caused a "mismatching a real number with list" type error.
# if your LabVIEW VI expects a fixed 3-element sentinel instead, change this to [-1.0, -1.0, -1.0].
SKIP_RETURN = []


# ===================================== customtkinter classes =====================================

class Moa:
    """
    Class: mother of all classes, parent and pass inputs from customtkinter.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self):
        super().__init__()
        self.rtn = ([],'','',[])


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
        # get user inputs
        path_folder = self.frm_ctl.ent_pth.get()
        # path_maskfd = os.path.join(path_folder, PARAMS_MAP)
        path_lsrimg = os.path.join(path_folder, PARAMS_LSR)
        path_tmpmsk = os.path.join(path_folder, PARAMS_TMP)
        path_bitsch = os.path.join(path_folder, PARAMS_BIT)
        path_scanct = os.path.join(path_folder, PARAMS_SCT)
        # arrange parameters into labview clusters (tuples)
        port_list = []
        port_length = len(pd.read_csv(
            path_bitsch, keep_default_na = False).values.tolist()[0][8].split(', '))
        for i in range(port_length):
            port_list.append(i+1)
        center_coordinates = pd.read_csv(
            path_scanct, keep_default_na = False, usecols=[1,2,3,4,5,6,7]).values.tolist()
        # # read cleave maps to create fov coordinate files
        # # so that empty areas are not included in the experiment construction
        fov = []
        for i in range(len(port_list)):
            mask = Image.open(os.path.join(path_folder, PARAMS_MAP, f"Round {i}.png"))
            cnt = 0
            df = []
            for j, coords in enumerate(center_coordinates):
                temp = mask.crop(coords[3:7])
                px_threshold = 10
                if count_non_white_pixel(temp) > px_threshold:
                    cnt += 1
                    df.append(center_coordinates[j])
            fov.append(cnt)
            dataframe = pd.DataFrame(df, columns=['x','y','z','w','n','e','s'])
            dataframe.to_csv(os.path.join(path_folder, PARAMS_MAP, f"Round {i}.csv"), index=True)
        # resume support: deduce where a previous (unintentionally terminated) run left off by
        # inspecting the last laser image saved in the image_laser folder, then persist that
        # (round, area) boundary. update_mask uses it to skip already-completed areas so the
        # experiment continues with the rest instead of restarting from the beginning.
        resume_point = find_resume_point(path_lsrimg)
        if resume_point is None:
            write_resume_point(path_folder, -1, -1)
            print("Resume: no existing laser images found, starting from round 0 area 0.")
        else:
            resume_round, resume_area = resume_point
            write_resume_point(path_folder, resume_round, resume_area)
            print(f"Resume: last saved laser image is round {resume_round} area {resume_area}.")
            print(f"Resume: skipping every area up to and including round {resume_round} "
                  f"area {resume_area}; the experiment will continue with the rest.")
        # return saved data
        self.rtn = (port_list, path_lsrimg, path_tmpmsk, fov)
        self.quit()
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

def parse_laser_image(filename):
    """
    Function: parse a per-FOV laser image filename into a (round, area) pair, or None.

    Uses the same convention as mercury_04: a per-FOV laser image is named so that
    filename[0:4] == 1000 + round and filename[5:9] == 1000 + area (both zero-indexed).
    Stitched round previews ("Round N.tif"/"Round N.png") and unrelated files are ignored.
    """
    # ignore stitched round previews and any non-image files
    if filename[:5] == "Round":
        return None
    root, ext = os.path.splitext(filename)
    if ext.lower() not in (".tif", ".tiff", ".png"):
        return None
    # the round/area digits live at fixed positions [0:4] and [5:9]
    if len(root) < 9:
        return None
    try:
        num_round = int(filename[0:4]) - 1000
        area = int(filename[5:9]) - 1000
    except ValueError:
        return None
    if num_round < 0 or area < 0:
        return None
    return (num_round, area)


def find_resume_point(laser_folder):
    """
    Function: scan the image_laser folder and return the last completed (round, area) in
    execution order (round-major, area-minor), or None if no laser image is present.
    """
    last_point = None
    try:
        filenames = os.listdir(laser_folder)
    except FileNotFoundError:
        return None
    for filename in filenames:
        parsed = parse_laser_image(filename)
        if parsed is None:
            continue
        if last_point is None or parsed > last_point:
            last_point = parsed
    return last_point


def write_resume_point(exp_folder, num_round, area):
    """
    Function: persist the resume boundary (round, area) so update_mask can skip completed areas.
    A boundary of (-1, -1) means "nothing to skip" (fresh run).
    """
    dataframe = pd.DataFrame({"round": [num_round], "area": [area]})
    dataframe.to_csv(os.path.join(exp_folder, PARAMS_RSM), index=False)


def read_resume_point(exp_folder):
    """
    Function: read the resume boundary written by app_exp; return a (round, area) tuple,
    or (-1, -1) when the file is missing or unreadable (i.e. skip nothing).
    """
    try:
        row = pd.read_csv(os.path.join(exp_folder, PARAMS_RSM)).values.tolist()[0]
        return (int(row[0]), int(row[1]))
    except (FileNotFoundError, IndexError, ValueError, KeyError):
        return (-1, -1)


def update_mask(img_folder, num_round, area):
    """
    Function: update and stretch temp cleave mask based on round/area number.
    return false if the update is unsuccessful.
    """
    # check for valid input
    if num_round < 0 or area < 0:
        print(f"Warning: invalid round/area combination: round {num_round} area {area}.")
        print(f"Warning: round {num_round} area {area} not executed.")
        return SKIP_RETURN
    # resume support: skip any (round, area) at or before the resume boundary written by app_exp.
    # these areas already have a saved laser image from a previous run, so returning the type-safe
    # empty "not executed" value keeps the laser from re-firing and lets the experiment continue
    # with the remaining areas. execution order is round-major, area-minor.
    # (use `< boundary` instead of `<= boundary` here if the last saved image should be redone.)
    exp_folder = os.path.dirname(img_folder)
    resume_round, resume_area = read_resume_point(exp_folder)
    if (resume_round, resume_area) != (-1, -1) and (num_round, area) <= (resume_round, resume_area):
        print(f"Resume: round {num_round} area {area} already completed, skipping.")
        return SKIP_RETURN
    # try constructing the mask
    try:
        # access cleave center coordinates (exp_folder computed above for the resume check)
        center_coord = pd.read_csv(os.path.join(exp_folder, PARAMS_MAP, f"Round {num_round}.csv"),
            keep_default_na = False, usecols=[1,2,3,4,5,6,7]).values.tolist()[area]
        # access cleave mask area
        tgt_mask = Image.open(os.path.join(exp_folder, PARAMS_MAP, f"Round {num_round}.png"))
        tgt_mask = tgt_mask.crop(center_coord[3:7])
        # # if the designated area is (nearly) blank, drop this area and return
        # px_threshold = 10
        # if count_non_white_pixel(tgt_mask) < px_threshold:
        #     print(f"Warning: designated area's pixel count is lower than {px_threshold}.")
        #     print(f"Warning: round {num_round} area {area} not executed.")
        #     return False
        # modify cleave mask
        # first create a [366, 366] or [732, 732] empty mask
        bg_width = 732
        bg_height = 732
        mod_mask = Image.new('P', [bg_width, bg_height], color = (255,255,255))
        # then paste the [300, 300] or [600, 600] cleave mask to the center
        overlay_width, overlay_height = tgt_mask.size
        x_init = round((bg_width - overlay_width) / 2)
        y_init = round((bg_height - overlay_height) / 2)
        mod_mask.paste(tgt_mask, (x_init, y_init))
        ###########################################################################################
        # # stretch the modified mask to [2304, 2304]
        # mod_mask = mod_mask.resize([2304, 2304]).rotate(180)
        # # crop out laser area
        # mod_mask = mod_mask.crop((208, 32, 208+1906, 32+2272))
        # # resize laser area to [1024, 1024]
        # mod_mask = mod_mask.resize([1024, 1024])
        # # flip vertically, then rotate 90 degrees to the left
        # mod_mask = mod_mask.transpose(Image.Transpose.FLIP_TOP_BOTTOM).rotate(90)
        ###########################################################################################
        # create new mask with 2304x2304 px and 200 px margin
        tmp_mask = Image.new('P', [2304+200,2304+200], color = (255,255,255))
        # stretch the modified mask to [2304, 2304]
        mod_mask = mod_mask.resize([2304, 2304])
        # paste modified mask onto the temporary mask (with 100 px margin)
        tmp_mask.paste(mod_mask, (100,100))
        # apply cropping, but from the perspective of bottom-right corner
        rota, vert, hori, x, y, w, h = load_mask_preset(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "default_calibration.yaml"), 1
        )
        mod_mask = tmp_mask.crop((
            2304 + 100 - h - y,
            2304 + 100 - w - x,
            2304 + 100 - y,
            2304 + 100 - x
        ))
        # rotate and flip based on mask calibration preset
        mod_mask = mod_mask.rotate(rota+180)
        if vert:
            mod_mask = mod_mask.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        if hori:
            mod_mask = mod_mask.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        # resize laser area to [1024, 1024]
        mod_mask = mod_mask.resize([1024, 1024])
        ###########################################################################################
        # save the modified image as the new temp mask
        rtn_mask = mod_mask.convert('L')
        rtn_mask = ImageOps.invert(rtn_mask)
        rtn_mask.save(os.path.join(exp_folder, PARAMS_TMP), format='PNG')
        return center_coord[0:3]
    except FileNotFoundError as e:
        print(f"Warning: {e}")
        print(f"Warning: round {num_round} area {area} not executed.")
        return SKIP_RETURN


def record_laser_coord(laser_img_folder_path, coords, num_round, execute_status):
    """
    Function: create/append (laser imaging) coordinates into a given csv file.
    if the file name/path does not exist, a file will be created.
    if the file name/path already exists, coordinates will be appended at the end of the file.
    """
    # find csv file name
    file = os.path.join(laser_img_folder_path, f"Round {num_round} (recorded).csv")
    # tolerate an empty / short coordinate list (e.g. a skipped or not-executed area) by padding
    # with NaN, so a record can still be written without an index error.
    x = coords[0] if len(coords) > 0 else float('nan')
    y = coords[1] if len(coords) > 1 else float('nan')
    z = coords[2] if len(coords) > 2 else float('nan')
    # if the file already exists, append new coordinates at the end of the file
    if os.path.exists(file):
        # read existing csv data as dataframe 1
        df1 = pd.read_csv(file, usecols=[1,2,3,4])
        # create new coordinates as dataframe 2
        df2 = pd.DataFrame({
            "x": [x],
            "y": [y],
            "z": [z],
            "exec": execute_status
        })
        # avoid concat empty dataframes (may cause empty rows)
        if df1.empty:
            df = df2
        else:
            df = pd.concat([df1, df2], ignore_index=True)
        df.to_csv(file, index=True)
    # if the file does not exist, create the file and store coordinates
    else:
        df = pd.DataFrame({
            "x": [x],
            "y": [y],
            "z": [z],
            "exec": execute_status
        })
        df.to_csv(file, index=True)


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
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
    try:
        return app.rtn
    except AttributeError:
        return ([],'','',[])
