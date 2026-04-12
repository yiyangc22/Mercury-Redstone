"""
Mercury 06: single cleave procedures, project version 1.25 (with python 3.9).
"""

import os
import customtkinter
from PIL import Image

from mercury_00 import load_mask_preset
from mercury_02 import FileInput, InputRow, PRES
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
        """
        # get mask path
        result, success = self.entry_mask.get_entry()
        if not success:
            self.lbl_inf.configure(text=result)
            self.lbl_inf.grid(row=6, column=0, padx=10, pady=(0,10), sticky="nesw", columnspan=1)
            return
        mask_path = result
        # get mask calibration preset
        result, success = self.entry_prst.get_entry()
        tpl = load_mask_preset(file_path=result, scaling_factor=1)
        if not tpl:
            self.lbl_inf.configure(
                text=f"Warning: cannot read {result} as a laser calibration preset"
            )
            self.lbl_inf.grid(row=6, column=0, padx=10, pady=(0,10), sticky="nesw", columnspan=1)
            return
        rota, vert, hori, x, y, w, h = tpl
        # get reference image size
        result, success = self.entry_prst.get_entry()
        ref = load_list_by_key(filepath=result, key=PARAMS_REF)
        if ref is None:
            self.lbl_inf.configure(
                text=f"Warning: cannot load preset {result} with key {PARAMS_REF}"
            )
            self.lbl_inf.grid(row=6, column=0, padx=10, pady=(0,10), sticky="nesw", columnspan=1)
            return
        if ref[0] != ref[1]:
            self.lbl_inf.configure(
                text=f"Warning: preset {result} has unequal image size {ref}"
            )
            self.lbl_inf.grid(row=6, column=0, padx=10, pady=(0,10), sticky="nesw", columnspan=1)
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
            # open a copy of the original mask, apply rotations/flips
            mod_mask = Image.open(mask_path)
            # create new mask with size of multichannel image and 200 px margin
            tmp_mask = Image.new('L', [PRES+200,PRES+200])
            # stretch the modified mask to the size of multichannel image
            mod_mask = mod_mask.resize([PRES, PRES])
            # paste modified mask onto the temporary mask (with 100 px margin)
            tmp_mask.paste(mod_mask, (100,100))
            # apply cropping, but from the perspective of bottom-right corner
            mod_mask = tmp_mask.crop((
                PRES + 100 - h - y,
                PRES + 100 - w - x,
                PRES + 100 - y,
                PRES + 100 - x
            ))
            # rotate and flip based on mask calibration preset
            mod_mask = mod_mask.rotate(rota+180)
            if vert:
                mod_mask = mod_mask.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            if hori:
                mod_mask = mod_mask.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            # check if mask image has the right size
            mw, mh = mod_mask.size
            if mw != mh or mw != PARAMS_MSS:
                mod_mask = mod_mask.resize([PARAMS_MSS, PARAMS_MSS])
            # use copy of the original mask instead
            base, ext = os.path.splitext(mask_path)
            mask_path = base+"_cleave"+ext
            mod_mask.save(mask_path)
            # change extension of mask image path to get laser image save path
            save_path = base+".tif"
            # export parameters
            self.rtn = (
                os.path.dirname(save_path),                                    # laser image folder
                os.path.basename(save_path),                                   # laser image name
                mask_path,                                                     # mask full path
                [round(parameter[0]),round(parameter[1]),round(parameter[2])], # x,y,z
                float(parameter[3]),                                           # cleave size
                float(parameter[4])                                            # exposure time
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

if __name__ == '__main__':
    print(mercury_06())
