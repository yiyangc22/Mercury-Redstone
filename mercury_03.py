"""
Mercury 03: fluid scheme constructor, project version 1.25 (with python 3.9).
"""

import os
import threading
import traceback

import yaml
import pandas as pd
import customtkinter
from PIL import Image, ImageOps

from mercury_00 import load_mask_preset
from mercury_01 import ctk_entry_warning
from mercury_02 import count_non_white_pixel, FileInput, InputRow, PopUpWindow, PRES

# from params import PARAMS_DTP
# from params import PARAMS_EXP
# from params import PARAMS_MCI
# from params import PARAMS_MSK
from params import PARAMS_LSR
from params import PARAMS_MAP
# from params import PARAMS_PLN
# from params import PARAMS_CRD
# from params import PARAMS_GLB
from params import PARAMS_SCT
from params import PARAMS_BIT
from params import PARAMS_TMP
from params import PARAMS_VER

# ctk window tilte
WINDOW_TXT = "Mercury III - Fluid Scheme Constructor"
# default mask calibration preset
PARAMS_MCP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "default_calibration.yaml")
# ctk frame parameters
PARAMS_LSP = [
    {"width": None, "txt": "Scan Size",              "val": 2.5,  "padx": (10,0), "type": float},
    {"width": None, "txt": "Min Pixel Threshold",    "val": 10,   "padx": (10,0), "type": int},
    {"width": None, "txt": "Temp Mask Size (px)",    "val": 1024, "padx": (10,0), "type": int},
    {"width": None, "txt": "Number of Fluidic Port", "val": 21,   "padx": (10,10), "type": int},
]


# ===================================== customtkinter classes =====================================

class Moa:
    """
    Class: mother of all classes, parent and pass inputs from customtkinter.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self):
        super().__init__()
        self.rtn = ([],'','',[],0.0,0,False,False,0.0,0.0,0.0,0.0)


class App(customtkinter.CTk, Moa):
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
        self.path_folder = None
        self.path_lsrimg = None
        self.path_tmpmsk = None
        self.path_bitsch = None
        self.path_scanct = None
        self.preset_pack = None
        self.scan_size = None
        self.px_threshold = None
        self.temp_mask_size = None
        self.port_length = None
        self.max_ports = None
        self.params = None
        self.pop_up = None
        self.pop_up_confirm = None
        self.txt_log = PARAMS_VER
        self.thread = threading.Thread(target=self.thread_export, daemon=True)
        # -------------------------------------- GUI setting --------------------------------------
        # prompt user for experiment folder path
        self.frm_ctl = FileInput(master=self, str_name=" Experiment Folder: ",)
        self.frm_ctl.grid(row=0, column=0, padx=10, pady=(10,5), sticky="nesw", columnspan=1)
        # prompt user for laser mask calibration preset
        self.frm_mcp = FileInput(
            master=self,
            str_name=" Calibration Preset: ",
            str_textvar=PARAMS_MCP,
            is_folder=False,
            init_dir=os.path.dirname(os.path.realpath(__file__))
        )
        self.frm_mcp.grid(row=1, column=0, padx=10, pady=(0,5), sticky="nesw", columnspan=1)
        # prompt user for laser scan parameters
        self.grid_input = InputRow(master=self, params=PARAMS_LSP)
        self.grid_input.grid(row=2, column=0, padx=10, pady=(5,0), sticky="nesw", columnspan=1)
        # commence button
        self.btn_cmc = customtkinter.CTkButton(master=self, text="Commence", command=self.app_exp)
        self.btn_cmc.grid(row=3, column=0, padx=10, pady=(5,10), sticky="nesw", columnspan=1)
        # create label to display information on the bottom of the frame
        self.lbl_inf = customtkinter.CTkLabel(
            master=self, font=customtkinter.CTkFont(size=10), width=610
        )
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on call ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def app_exp(self):
        """
        Function: commence the export of collected user inputs.
        """
        # read experiment folder, check if it's a valid folder path
        self.path_folder, successful = self.frm_ctl.get_entry(check_for_folder=True)
        if not successful:
            self.lbl_inf.configure(text=self.path_folder)
            self.lbl_inf.grid(row=6, column=0, padx=10, pady=(0,10), sticky="nesw", columnspan=1)
            return
        self.path_lsrimg = os.path.join(self.path_folder, PARAMS_LSR)
        self.path_tmpmsk = os.path.join(self.path_folder, PARAMS_TMP)
        self.path_bitsch = os.path.join(self.path_folder, PARAMS_BIT)
        self.path_scanct = os.path.join(self.path_folder, PARAMS_SCT)
        if not os.path.isdir(self.path_lsrimg):
            ctk_entry_warning(self.frm_ctl.ent_pth)
            self.lbl_inf.configure(
                text=f"Warning: no folder named \"{self.path_lsrimg}\" in \"{self.path_folder}\""
            )
            self.lbl_inf.grid(row=6, column=0, padx=10, pady=(0,10), sticky="nesw", columnspan=1)
            return
        for path in (self.path_bitsch, self.path_scanct):
            if not os.path.isfile(path):
                ctk_entry_warning(self.frm_ctl.ent_pth)
                self.lbl_inf.configure(
                    text=f"Warning: no file named \"{path}\" in \"{self.path_folder}\""
                )
                self.lbl_inf.grid(
                    row=6, column=0, padx=10, pady=(0,10), sticky="nesw", columnspan=1
                )
                return
        # read mask calibration preset, check if it's a valid preset
        result, successful = self.frm_mcp.get_entry(check_for_folder=False)
        if not successful:
            self.lbl_inf.configure(text=result)
            self.lbl_inf.grid(row=6, column=0, padx=10, pady=(0,10), sticky="nesw", columnspan=1)
            return
        # if successful, check if mask preset is valid, then update parameter and clear info label
        self.preset_pack = load_mask_preset(result, scaling_factor=1)
        # read inputs, show error if type conversion failed
        result, successful = self.grid_input.get_entry()
        if not successful:
            self.lbl_inf.configure(text=result)
            self.lbl_inf.grid(row=6, column=0, padx=10, pady=(0,10), sticky="nesw", columnspan=1)
            return
        self.scan_size = result[0]
        self.px_threshold = result[1]
        self.temp_mask_size = result[2]
        self.max_ports = result[3]
        self.port_length = len(pd.read_csv(
            self.path_bitsch, keep_default_na = False).values.tolist()[0][8].split(', ')
        )
        # if successful, update app class parameters for thread functions, clear information label
        self.params = result
        self.lbl_inf.grid_forget()
        # check if port length exceeds user defined maximum port number, prompt user confirmations
        if self.port_length > self.max_ports:
            msg = f"Caution: {self.port_length} fluidic rounds required, "
            msg += f"but {self.max_ports} ports are allowed.\n"
            msg += f"Last {self.port_length-self.max_ports} round(s) will be discarded. Proceed?"
            self.pop_up_confirm = ConfirmWindow(
                self,
                title="Action Required",
                label_text=msg,
                label_wrap=390,
                geometry="400x120"
            )
            self.pop_up_confirm.after(10, self.pop_up_confirm.lift)
        else:
            self.enter_thread()
    # ---------------------------------------------------------------------------------------------
    def enter_thread(self):
        """
        Function: initialize grid submask construction in a separate thread.
        """
        # initialize a toplevel window (if one already exists, focus it into view)
        self.pop_up = PopUpWindow(
            self,
            title="Progress",
            label_text="Initializing ...",
            label_wrap=390,
            geometry="400x120"
        )
        self.pop_up.after(10, self.pop_up.lift)
        self.thread = threading.Thread(target=self.thread_export, daemon=True)
        self.thread.start()
    # ---------------------------------------------------------------------------------------------
    def thread_export(self):
        """
        Function: run grid submask construction in a separate thread.
        """
        self.txt_log += "\nentering thread"
        self.pop_up.set_text(
            text="Solving project scan scheme ..."
        )
        # calculate port list and port lengths
        port_list = []
        self.txt_log += f"\nrequire {self.port_length} rounds, user allowed max {self.max_ports}"
        self.port_length = min(self.port_length, self.max_ports)
        for i in range(self.port_length):
            port_list.append(i+1)
        # change temp mask size
        img = Image.new('L', [self.temp_mask_size, self.temp_mask_size])
        img.save(self.path_tmpmsk)
        self.txt_log += f"\ntemp mask now {self.temp_mask_size}x{self.temp_mask_size} px, mode L"
        # get center coordinates for scan areas
        center_coordinates = pd.read_csv(
            self.path_scanct, keep_default_na = False, usecols=[1,2,3,4,5,6,7]).values.tolist()
        # read cleave maps to create fov coordinate files
        # so that empty areas are not included in the experiment construction
        self.txt_log += "\nmapping scan coordinates, save as csv\nRound(s):"
        try:
            round_fov_counts = []
            for i in range(len(port_list)):
                self.pop_up.set_text(
                    text=f"Mapping scan coordinates ...\n(round {i}/{len(port_list)})"
                )
                self.pop_up.set_progress(i/len(port_list))
                mask = Image.open(os.path.join(self.path_folder, PARAMS_MAP, f"Round {i}.png"))
                cnt = 0
                df = []
                for j, coords in enumerate(center_coordinates):
                    temp = mask.crop(coords[3:7])
                    if count_non_white_pixel(temp) > self.px_threshold:
                        cnt += 1
                        df.append(center_coordinates[j])
                round_fov_counts.append(cnt)
                dataframe = pd.DataFrame(df, columns=['x','y','z','w','n','e','s'])
                dataframe.to_csv(
                    os.path.join(self.path_folder, PARAMS_MAP, f"Round {i}.csv"), index=True
                )
                self.txt_log += f"{i}, "
            # return saved data
            rota, vert, hori, x, y, w, h = self.preset_pack
            self.rtn = (
                port_list,
                self.path_lsrimg,
                self.path_tmpmsk,
                round_fov_counts,
                self.scan_size,
                rota, vert, hori, x, y, w, h
            )
            self.txt_log += "successfully processed\ndone"
            self.end_task()
        except (ValueError, IndexError, TypeError, RuntimeError, FileNotFoundError) as e:
            traceback.print_exc()
            self.pop_up.set_text(
                text=f"Cannot map scan coordinates - {e}\n** Restart program to try again. **"
            )
            self.txt_log += f"\n{e}"
            with open(
                os.path.join(self.path_folder, "mercury_03_log.txt"), 'w', encoding="utf-8"
            ) as file:
                file.write(self.txt_log)
            return
    # ---------------------------------------------------------------------------------------------
    def on_closing(self):
        """
        Function: enforce quit manually before closing.
        """
        self.quit()
    # ---------------------------------------------------------------------------------------------
    def end_task(self):
        """Function: finish export and prompt for user action."""
        # save logs
        self.txt_log += "\nall process finished with no error"
        with open(
            os.path.join(self.path_folder, "mercury_03_log.txt"), 'w', encoding="utf-8"
        ) as file:
            file.write(self.txt_log)
        # prompt user to exit
        self.pop_up.set_text(text="Finished! You may exit the program now.")
        # show option to exit
        self.pop_up = customtkinter.CTkButton(
            master=self,
            text="Exit and return to LabVIEW",
            command=self.on_closing
        )


class ConfirmWindow(customtkinter.CTkToplevel):
    """
    Class: ctk top level window for prompting user confirmation.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, master, title, label_text, label_wrap=None, geometry=None, **kwargs):
        super().__init__(master, **kwargs)
        # ---------------------------------- application setting ----------------------------------
        self.title(title)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.protocol("WM_DELETE_WINDOW", lambda: self.on_closing(False))
        if geometry is not None:
            self.geometry(geometry)
        # -------------------------------------- GUI setting --------------------------------------
        self.lbl_txt = customtkinter.CTkLabel(master=self, text=label_text)
        self.lbl_txt.grid(row=0, column=0, padx=10, pady=5, sticky="nesw", columnspan=2)
        if label_wrap is not None:
            self.lbl_txt.configure(wraplength=label_wrap)
        self.button_t = customtkinter.CTkButton(
            master=self,
            text="Yes",
            command=lambda: self.on_closing(True)
        )
        self.button_t.grid(row=1, column=0, padx=(10,0), pady=(0,10), sticky="nesw")
        self.button_t = customtkinter.CTkButton(
            master=self,
            text="No",
            command=lambda: self.on_closing(False),
            fg_color="transparent",
            border_color="grey",
            border_width=1
        )
        self.button_t.grid(row=1, column=1, padx=(5,10), pady=(0,10), sticky="nesw")
    # ---------------------------------------------------------------------------------------------
    def on_closing(self, result:bool):
        """Function: enforce quit manually before closing."""
        if result:
            self.master.enter_thread()
        self.destroy()


# ===================================== independent functions =====================================

def update_mask(img_folder, num_round, area, rota, vert, hori, x, y, w, h):
    """
    Function: update temp cleave mask based on round/area number, and return the
    stage coordinates (compensated for the laser-vs-camera FOV offset).
    return [[],[],[]] if the update is unsuccessful.

    Calibration (rota, vert, hori, x, y, w, h) describes the forward optics
    that take a mask M -> camera image: rotate(rota) -> flip_v -> flip_h ->
    resize_to(w, h) -> place_at(x, y) in a PRES x PRES camera frame. To make
    the projected pattern match the cleave-map tile, we apply the inverse of
    the rotation and flips here; the device handles the resize/translate.

    Stage offset: mercury_02 stores stage (x_um, y_um) using camera-aligned
    coordinates, but the laser FOV sits at (x, y, w, h) in camera pixels --
    not at the camera center. We shift the returned stage coordinates by the
    laser-vs-camera-center vector so the laser ends up where the cleave map
    intended, instead of where the camera was looking.
    """
    # camera FOV side length in micrometers (square FOV -- adjust for your scope)
    CAM_FOV_UM = 366
    # check for valid input
    if num_round < 0 or area < 0:
        print(f"Warning: invalid round/area combination: round {num_round} area {area}.")
        print(f"Warning: round {num_round} area {area} not executed.")
        return [[],[],[]]
    # try constructing the mask
    try:
        # access cleave center coordinates and the cleave-map tile for this area
        exp_folder = os.path.dirname(img_folder)
        center_coord = pd.read_csv(os.path.join(exp_folder, PARAMS_MAP, f"Round {num_round}.csv"),
            keep_default_na = False, usecols=[1,2,3,4,5,6,7]).values.tolist()[area]
        tgt_mask = Image.open(os.path.join(exp_folder, PARAMS_MAP, f"Round {num_round}.png"))
        tgt_mask = tgt_mask.crop(center_coord[3:7]).convert('L')
        # fill the laser device's mask canvas with the tile (device will rescale to FOV)
        tmp_mask = Image.open(os.path.join(exp_folder, PARAMS_TMP))
        mod_mask = tgt_mask.resize(tmp_mask.size, resample=Image.NEAREST)
        # pre-distort: invert (rotate -> flip_v -> flip_h) by applying inverses in reverse order
        if hori:
            mod_mask = mod_mask.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        if vert:
            mod_mask = mod_mask.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        if rota % 360:
            mod_mask = mod_mask.rotate(-rota, expand=False, fillcolor=255)
        # invert (cleave map: white = skip; laser device: white = fire) and save
        rtn_mask = ImageOps.invert(mod_mask)
        rtn_mask.save(os.path.join(exp_folder, PARAMS_TMP), format='PNG')
        # --- stage coordinate compensation for laser-vs-camera FOV offset ---
        # laser FOV center vs camera FOV center, in camera pixels:
        offset_px_x = (x + w / 2) - PRES / 2
        offset_px_y = (y + h / 2) - PRES / 2
        # convert pixel offset to stage micrometers using camera scale.
        # NOTE: stage Y axis is inverted relative to image Y axis (mercury_02
        # builds rows with `int_start_y_um - row*laser_h_um`), so the stage
        # offset Y component picks up an extra negative sign.
        cam_um_per_px = CAM_FOV_UM / PRES
        offset_um_x = offset_px_x * cam_um_per_px
        offset_um_y = -offset_px_y * cam_um_per_px
        # to fire the laser where the cleave map intended, move the stage
        # opposite to the laser-vs-camera offset.
        cx, cy, cz = center_coord[0:3]
        cx -= offset_um_x
        cy -= offset_um_y
        return [cx, cy, cz]
    except FileNotFoundError as e:
        print(f"Warning: {e}")
        print(f"Warning: round {num_round} area {area} not executed.")
        return [[],[],[]]


def record_laser_coord(laser_img_folder_path, coords, num_round, execute_status):
    """
    Function: create/append (laser imaging) coordinates into a given csv file.
    if the file name/path does not exist, a file will be created.
    if the file name/path already exists, coordinates will be appended at the end of the file.
    """
    # find csv file name
    file = os.path.join(laser_img_folder_path, f"Round {num_round} (recorded).csv")
    # if the file already exists, append new coordinates at the end of the file
    if os.path.exists(file):
        # read existing csv data as dataframe 1
        df1 = pd.read_csv(file, usecols=[1,2,3,4])
        # create new coordinates as dataframe 2
        df2 = pd.DataFrame({
            "x": [coords[0]],
            "y": [coords[1]],
            "z": [coords[2]],
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
            "x": [coords[0]],
            "y": [coords[1]],
            "z": [coords[2]],
            "exec": execute_status
        })
        df.to_csv(file, index=True)


def load_list_by_key(filepath, key):
    """
    Function: load a YAML file and retrieves a specific list by its key.
    """
    with open(filepath, 'r', encoding="utf-8") as file_descriptor:
        try:
            # use safe_load for security when dealing with untrusted sources
            data = yaml.safe_load(file_descriptor)
            # loaded data must be a python dictionary or list
            if isinstance(data, dict) and key in data:
                return data[key]
            # return none if no matching result is found
            print(f"Key '{key}' not found or data is not a dictionary.")
            return None
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file: {e}")
            return None


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
    app.attributes("-topmost", True)
    app.after_idle(app.attributes, "-topmost", False)
    app.after(10, app.focus)
    app.mainloop()
    try:
        return app.rtn
    except AttributeError:
        return ([],'','',[],0.0,0,False,False,0.0,0.0,0.0,0.0)
