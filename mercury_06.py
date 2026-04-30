"""
Mercury 06: single cleave procedures, project version 1.25 (with python 3.9).
"""

import os
import customtkinter
from PIL import Image

from mercury_00 import load_mask_preset
from mercury_02 import FileInput, InputRow, PRES, MRES
from mercury_03 import load_list_by_key

# from params import PARAMS_DTP
# from params import PARAMS_EXP
# from params import PARAMS_MCI
# from params import PARAMS_MSK
# from params import PARAMS_LSR
# from params import PARAMS_MAP
# from params import PARAMS_PLN
# from params import PARAMS_CRD
# from params import PARAMS_GLB
# from params import PARAMS_SCT
# from params import PARAMS_BIT
# from params import PARAMS_TMP
# from params import PARAMS_VER

# ctk window tilte
WINDOW_TXT = "Mercury VI - Single Cleave Procedure"
# default mask calibration preset
PARAMS_MCP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "default_calibration.yaml")
# ctk frame parameters
PARAMS_SZE = SZE = 2.5
PARAMS_REF = 'ref'
PARAMS_MSS = 1024
PARAMS_LSP = [
    {"width": None, "txt": "Scan Size",              "val": SZE, "padx": (10,0),  "type": float},
    {"width": None, "txt": "Exposure Time",          "val": 0.1, "padx": (10,10),  "type": float},
]


# ===================================== customtkinter classes =====================================

class Moa:
    """
    Class: mother of all classes, parent and pass inputs from customtkinter.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self):
        super().__init__()
        self.rtn = ('', '', '', [], PARAMS_SZE, 0.0)


class App(customtkinter.CTk, Moa):
    """
    Class: main application window and customtkinter main loop.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, x = None, y = None, z = None):
        super().__init__()
        # ---------------------------------- application setting ----------------------------------
        self.title(WINDOW_TXT)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        # store input xyz value into ctk app mainloop
        self.x = x
        self.y = y
        self.z = z
        self.frame_params = [
            {"width": None, "txt": "Scan Center X", "val": x, "padx": (10,0),  "type": float},
            {"width": None, "txt": "Scan Center Y", "val": y, "padx": (10,0),  "type": float},
            {"width": None, "txt": "Scan Center Z", "val": z, "padx": (10,0),  "type": float},
        ] + PARAMS_LSP
        # -------------------------------------- GUI setting --------------------------------------
        # set entry frames for mask and laser image path
        self.entry_mask = FileInput(
            master=self,
            str_name="Mask Image Full Path:",
            is_folder=False,
            init_dir=os.path.dirname(os.path.abspath(__file__))
        )
        self.entry_mask.grid(row=1, column=0, padx=10, pady=(10,0), sticky="ew")
        # mask calibration preset path
        self.entry_prst = FileInput(
            master=self,
            str_name="Calibration Preset:",
            str_textvar=PARAMS_MCP,
            is_folder=False,
            init_dir=os.path.dirname(os.path.abspath(__file__))
        )
        self.entry_prst.grid(row=3, column=0, padx=10, pady=(5,0), sticky="ew")
        # set control frames for laser parameters
        self.frame_ctrl = InputRow(
            master=self,
            params=self.frame_params
        )
        self.frame_ctrl.grid(row=4, column=0, padx=10, pady=(5,0), sticky="ew")
        # set commence button
        self.btn_cmc = customtkinter.CTkButton(master=self, text="Commence", command=self.app_exp)
        self.btn_cmc.grid(row=5, column=0, padx=10, pady=(5,10), sticky="ew")
        # create label to display information on the bottom of the frame
        self.lbl_inf = customtkinter.CTkLabel(
            master=self, font=customtkinter.CTkFont(size=10)
        )
    # ---------------------------------------------------------------------------------------------
    def app_exp(self):
        """
        Function: commence the export of collected user inputs.

        If the calibration preset entry is left blank, the mask is passed
        through with only a resize to the laser device's expected size --
        no rotation, flip, FOV crop, or stage offset compensation. This
        produces a "raw" laser illumination pattern that the user can
        capture and feed back into mercury_00 to derive the calibration.
        """
        # get mask path (required)
        result, success = self.entry_mask.get_entry()
        if not success:
            self.lbl_inf.configure(text=result)
            self.lbl_inf.grid(row=6, column=0, padx=10, pady=(0,10), sticky="nesw", columnspan=1)
            return
        mask_path = result
        # get mask calibration preset (optional: empty entry => raw mode)
        preset_text = self.entry_prst.ent_pth.get().strip()
        use_preset = bool(preset_text)
        rota, vert, hori, x, y, w, h = 0, False, False, 0, 0, 0, 0
        if use_preset:
            result, success = self.entry_prst.get_entry()
            tpl = load_mask_preset(file_path=result, scaling_factor=1)
            if not tpl:
                self.lbl_inf.configure(
                    text=f"Warning: cannot read {result} as a laser calibration preset"
                )
                self.lbl_inf.grid(
                    row=6, column=0, padx=10, pady=(0,10), sticky="nesw", columnspan=1
                )
                return
            rota, vert, hori, x, y, w, h = tpl
            # get reference image size (preserved sanity check from previous version)
            ref = load_list_by_key(filepath=result, key=PARAMS_REF)
            if ref is None:
                self.lbl_inf.configure(
                    text=f"Warning: cannot load preset {result} with key {PARAMS_REF}"
                )
                self.lbl_inf.grid(
                    row=6, column=0, padx=10, pady=(0,10), sticky="nesw", columnspan=1
                )
                return
            if ref[0] != ref[1]:
                self.lbl_inf.configure(
                    text=f"Warning: preset {result} has unequal image size {ref}"
                )
                self.lbl_inf.grid(
                    row=6, column=0, padx=10, pady=(0,10), sticky="nesw", columnspan=1
                )
            else:
                ref = round(ref[0])
        # get xyz coordinates and scan parameters
        result, success = self.frame_ctrl.get_entry()
        if not success:
            self.lbl_inf.configure(text=result)
            self.lbl_inf.grid(row=6, column=0, padx=10, pady=(0,10), sticky="nesw", columnspan=1)
            return
        parameter = result
        # process coordinates, calibrations, and mask image
        try:
            mod_mask = Image.open(mask_path).convert('L')
            if use_preset:
                # treat the input as a desired camera-space image, then extract
                # the laser-FOV portion (in camera pixels)
                mod_mask = mod_mask.resize([PRES, PRES], resample=Image.NEAREST)
                mod_mask = mod_mask.crop((x, y, x + w, y + h))
                # resize to the laser device's expected mask size
                mod_mask = mod_mask.resize(
                    [PARAMS_MSS, PARAMS_MSS], resample=Image.NEAREST
                )
                # pre-distort: invert the optics' (rotate -> flip_v -> flip_h)
                # by applying the inverses in reverse order
                if hori:
                    mod_mask = mod_mask.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                if vert:
                    mod_mask = mod_mask.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                if rota % 360:
                    mod_mask = mod_mask.rotate(-rota, expand=False, fillcolor=255)
            else:
                # raw mode: only resize the mask, no rotation/flip/FOV crop
                mod_mask = mod_mask.resize(
                    [PARAMS_MSS, PARAMS_MSS], resample=Image.NEAREST
                )
            # save the processed mask alongside the original
            base, ext = os.path.splitext(mask_path)
            mask_path = base + "_cleave" + ext
            mod_mask.save(mask_path)
            # change extension of mask image path to get laser image save path
            save_path = base + ".tif"
            # stage coordinates: compensate for laser-vs-camera FOV offset
            # (only when a preset is provided -- raw mode passes xyz through)
            cx = float(parameter[0])
            cy = float(parameter[1])
            cz = float(parameter[2])
            if use_preset:
                offset_px_x = (x + w / 2) - PRES / 2
                offset_px_y = (y + h / 2) - PRES / 2
                cam_um_per_px = MRES / PRES
                # NOTE: stage Y axis inverted relative to image Y (see mercury_02
                # tile loop); flip the sign on the Y component accordingly.
                offset_um_x = offset_px_x * cam_um_per_px
                offset_um_y = -offset_px_y * cam_um_per_px
                cx -= offset_um_x
                cy -= offset_um_y
            # export parameters
            self.rtn = (
                os.path.dirname(save_path),                # laser image folder
                os.path.basename(save_path),               # laser image name
                mask_path,                                 # mask full path
                [round(cx), round(cy), round(cz)],         # x, y, z
                float(parameter[3]),                       # cleave size
                float(parameter[4])                        # exposure time
            )
        except (ValueError, TypeError, FileNotFoundError, AttributeError) as e:
            self.lbl_inf.configure(text=e)
            self.lbl_inf.grid(row=6, column=0, padx=10, pady=(0,10), sticky="nesw", columnspan=1)
            return
        # reset information lable once all parameters are checked
        self.lbl_inf.grid_forget()
        self.quit()

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
    app.attributes("-topmost", True)
    app.after_idle(app.attributes, "-topmost", False)
    app.after(10, app.focus)
    app.mainloop()
    try:
        return app.rtn
    except AttributeError:
        return ('', '', '', [], PARAMS_SZE, 0.0)
