"""
Mercury 05: fluidic master control, project version 1.26 (with python 3.9).
"""

import math
import customtkinter
from tkinter import filedialog

from mercury_01 import ctk_entry_warning

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

WINDOW_TXT = "Mercury V - Fluidic Master Control"
WINDOW_RES = "900x600"
# -------------------------------------------------------------------------------------------------
# PHYSICAL PORT CONFIGURATION -- edit this dictionary if the plumbing/roles change.
#   key   = physical valve port name ("A1".."A24" on valve 1, "B1".."B24" on valve 2)
#   value = (num, role, label)
#       num   : command port number returned in each tuple (None if not addressable)
#       role  : "barcode" | "pbs" | "ligase" | "air" | "disabled"
#       label : text shown beside the port's entries
# Valve-1 port A24 is the valve 1-2 daisy-chain connection and is shown disabled.
# -------------------------------------------------------------------------------------------------
PARAMS_CFG = {
    # ---- Valve 1 (A) ----
    "A1":  (1,    "barcode",  "A1  Barcode 1"),
    "A2":  (2,    "barcode",  "A2  Barcode 2"),
    "A3":  (3,    "barcode",  "A3  Barcode 3"),
    "A4":  (4,    "barcode",  "A4  Barcode 4"),
    "A5":  (5,    "barcode",  "A5  Barcode 5"),
    "A6":  (6,    "barcode",  "A6  Barcode 6"),
    "A7":  (7,    "barcode",  "A7  Barcode 7"),
    "A8":  (8,    "barcode",  "A8  Barcode 8"),
    "A9":  (9,    "barcode",  "A9  Barcode 9"),
    "A10": (10,   "barcode",  "A10  Barcode 10"),
    "A11": (11,   "barcode",  "A11  Barcode 11"),
    "A12": (12,   "barcode",  "A12  Barcode 12"),
    "A13": (13,   "barcode",  "A13  Barcode 13"),
    "A14": (14,   "barcode",  "A14  Barcode 14"),
    "A15": (15,   "barcode",  "A15  Barcode 15"),
    "A16": (16,   "barcode",  "A16  Barcode 16"),
    "A17": (17,   "barcode",  "A17  Barcode 17"),
    "A18": (18,   "barcode",  "A18  Barcode 18"),
    "A19": (19,   "barcode",  "A19  Barcode 19"),
    "A20": (20,   "barcode",  "A20  Barcode 20"),
    "A21": (21,   "barcode",  "A21  Barcode 21"),
    "A22": (22,   "barcode",  "A22  Barcode 22"),
    "A23": (23,   "pbs",      "A23  PBS wash"),
    "A24": (None, "disabled", "A24  (disabled)"),
    # ---- Valve 2 (B) ----
    "B1":  (24,   "barcode",  "B1  Barcode 23"),
    "B2":  (25,   "barcode",  "B2  Barcode 24"),
    "B3":  (26,   "barcode",  "B3  Barcode 25"),
    "B4":  (27,   "barcode",  "B4  Barcode 26"),
    "B5":  (28,   "barcode",  "B5  Barcode 27"),
    "B6":  (29,   "barcode",  "B6  Barcode 28"),
    "B7":  (30,   "barcode",  "B7  Barcode 29"),
    "B8":  (31,   "barcode",  "B8  Barcode 30"),
    "B9":  (32,   "barcode",  "B9  Barcode 31"),
    "B10": (33,   "barcode",  "B10  Barcode 32"),
    "B11": (34,   "barcode",  "B11  Barcode 33"),
    "B12": (35,   "barcode",  "B12  Barcode 34"),
    "B13": (36,   "barcode",  "B13  Barcode 35"),
    "B14": (37,   "barcode",  "B14  Barcode 36"),
    "B15": (38,   "barcode",  "B15  Barcode 37"),
    "B16": (39,   "barcode",  "B16  Barcode 38"),
    "B17": (40,   "barcode",  "B17  Barcode 39"),
    "B18": (41,   "barcode",  "B18  Barcode 40"),
    "B19": (42,   "barcode",  "B19  Barcode 41"),
    "B20": (43,   "barcode",  "B20  Barcode 42"),
    "B21": (44,   "air",      "B21  (air)"),
    "B22": (45,   "ligase",   "B22  Ligase buffer"),
    "B23": (46,   "air",      "B23  (air)"),
    "B24": (47,   "air",      "B24  (air)"),
}
# scrollable columns: (section title, physical-port-name prefix)
PARAMS_LAY = [("Valve 1  -  ports A1-A24", "A"),
              ("Valve 2  -  ports B1-B24", "B")]
# message colors: error / warning and success
PARAMS_ECL = "#B62B24"
PARAMS_OCL = "#2FA572"


# ===================================== customtkinter classes =====================================

class Moa:
    """
    Class: mother of all classes, parent and pass inputs from customtkinter.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self):
        super().__init__()
        self.rtn = []


class PortCell(customtkinter.CTkFrame):
    """
    Class: ctk frame for a single fluidic port (label + flow-rate + flow-volume entries).
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, master, port_name, num, role, label, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="grey23")
        self.port_name = port_name
        self.port_num = num
        self.role = role
        self.disabled = (role == "disabled")
        # let both entry columns share the extra horizontal space
        self.grid_columnconfigure(1, weight=1, uniform="entry")
        self.grid_columnconfigure(2, weight=1, uniform="entry")
        # -------------------------------------- GUI setting --------------------------------------
        # port label (role-aware, not bolded)
        self.lbl_prt = customtkinter.CTkLabel(master=self, width=140, text=label, anchor="w")
        if self.disabled:
            self.lbl_prt.configure(text_color="gray50")
        self.lbl_prt.grid(row=0, column=0, padx=(8,6), pady=6, sticky="nsw")
        # flow rate entry
        self.inp_flw = customtkinter.CTkEntry(
            master = self,
            width = 120,
            placeholder_text = ("" if self.disabled else "Rate (uL/min)")
        )
        self.inp_flw.grid(row=0, column=1, padx=4, pady=6, sticky="ew")
        # flow volume entry
        self.inp_vol = customtkinter.CTkEntry(
            master = self,
            width = 120,
            placeholder_text = ("" if self.disabled else "Volume (uL)")
        )
        self.inp_vol.grid(row=0, column=2, padx=(4,8), pady=6, sticky="ew")
        # a disabled port (e.g. the daisy-chain link) takes no input
        if self.disabled:
            self.inp_flw.configure(state="disabled")
            self.inp_vol.configure(state="disabled")
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on call ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def read(self):
        """Function: return (flow_rate_str, flow_volume_str), whitespace stripped."""
        return self.inp_flw.get().strip(), self.inp_vol.get().strip()
    # ---------------------------------------------------------------------------------------------
    def set(self, flow, volume):
        """Function: overwrite the flow-rate and flow-volume entries with given strings."""
        for entry, value in ((self.inp_flw, flow), (self.inp_vol, volume)):
            entry.delete(0, "end")
            entry.insert(0, value)
    # ---------------------------------------------------------------------------------------------
    def warn(self, flow=False, volume=False):
        """Function: briefly flash the flow-rate and/or flow-volume entry to signal an error."""
        if flow:
            ctk_entry_warning(self.inp_flw)
        if volume:
            ctk_entry_warning(self.inp_vol)


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
        self.grid_rowconfigure(1, weight=1)
        self.rtn = []
        self.cells:list[PortCell] = []
        # -------------------------------------- GUI setting --------------------------------------
        # scrollable port grid (valve 1 on the left column, valve 2 on the right column)
        self.frm_lst = customtkinter.CTkScrollableFrame(master=self, corner_radius=5)
        self.frm_lst.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.frm_lst.grid_columnconfigure(0, weight=1, uniform="valve")
        self.frm_lst.grid_columnconfigure(1, weight=1, uniform="valve")
        self._populate()
        # message label (only gridded when there is something to report)
        self.lbl_inf = customtkinter.CTkLabel(
            master = self,
            anchor = "w",
            font = customtkinter.CTkFont(size=12)
        )
        # button row: load / save configuration and commence
        self.frm_btn = customtkinter.CTkFrame(master=self, fg_color="transparent")
        self.frm_btn.grid(row=3, column=0, padx=10, pady=(0,10), sticky="nesw")
        self.frm_btn.grid_columnconfigure(0, weight=1)
        self.frm_btn.grid_columnconfigure(1, weight=1)
        self.frm_btn.grid_columnconfigure(2, weight=2)
        self.btn_lod = customtkinter.CTkButton(
            master=self.frm_btn, text="Load Config", command=self.load_config,
            fg_color="transparent", border_width=1
        )
        self.btn_lod.grid(row=0, column=0, padx=(0,5), sticky="nesw")
        self.btn_sav = customtkinter.CTkButton(
            master=self.frm_btn, text="Save Config", command=self.save_config,
            fg_color="transparent", border_width=1
        )
        self.btn_sav.grid(row=0, column=1, padx=5, sticky="nesw")
        self.btn_cmc = customtkinter.CTkButton(
            master=self.frm_btn, text="Commence", command=self.app_exp
        )
        self.btn_cmc.grid(row=0, column=2, padx=(5,0), sticky="nesw")
    # ---------------------------------------------------------------------------------------------
    def _populate(self):
        """Function: fill the scrollable frame with one PortCell per configured port."""
        for col, (title, prefix) in enumerate(PARAMS_LAY):
            header = customtkinter.CTkLabel(
                master = self.frm_lst,
                text = title,
                anchor = "w",
                font = customtkinter.CTkFont(size=14)
            )
            header.grid(row=0, column=col, padx=5, pady=(0,5), sticky="nesw")
            row = 1
            for name, (num, role, label) in PARAMS_CFG.items():
                if not name.startswith(prefix):
                    continue
                cell = PortCell(
                    master=self.frm_lst, port_name=name, num=num, role=role, label=label
                )
                cell.grid(row=row, column=col, padx=5, pady=(0,5), sticky="nesw")
                self.cells.append(cell)
                row += 1
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on call ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def app_exp(self):
        """
        Function: collect valid port commands, flash offending inputs, commence if error-free.
        """
        # clear any previous message
        self.lbl_inf.grid_forget()
        commands = []
        has_error = False
        for cell in self.cells:
            # the disabled daisy-chain port carries no command
            if cell.disabled:
                continue
            flw_str, vol_str = cell.read()
            # a port left entirely blank is simply not used this round
            if flw_str == "" and vol_str == "":
                continue
            # both fields are required once one is filled; each must convert to an int
            flw_val = self._to_int(flw_str)
            vol_val = self._to_int(vol_str)
            bad_flw = flw_val is None
            bad_vol = vol_val is None
            if bad_flw or bad_vol:
                cell.warn(flow=bad_flw, volume=bad_vol)
                has_error = True
            else:
                commands.append((cell.port_num, flw_val, vol_val))
        # if any port was partially filled or misformatted, show a note and do not commence
        if has_error:
            self._info(
                "  Warning: missing or incorrect format (int/float).",
                error=True
            )
            return
        # return commands ordered by port number, then end the main loop
        self.rtn = commands
        self.quit()
    # ---------------------------------------------------------------------------------------------
    def save_config(self):
        """Function: write every used port's (rate, volume) to a tab-separated configuration file."""
        path = filedialog.asksaveasfilename(
            parent = self,
            title = "Save fluidic configuration",
            defaultextension = ".tsv",
            filetypes = [("Tab-separated values", "*.tsv"), ("All files", "*.*")]
        )
        if not path:
            return
        lines = ["port\trate\tvolume"]
        for cell in self.cells:
            if cell.disabled:
                continue
            flw_str, vol_str = cell.read()
            lines.append(f"{cell.port_name}\t{flw_str}\t{vol_str}")
        try:
            with open(path, "w", encoding="utf-8") as file:
                file.write("\n".join(lines) + "\n")
        except OSError as err:
            self._info(f"  Could not save configuration: {err}", error=True)
            return
        self._info(f"  Saved configuration to {path}", error=False)
    # ---------------------------------------------------------------------------------------------
    def load_config(self):
        """Function: read a tab-separated configuration file and repopulate the port entries."""
        path = filedialog.askopenfilename(
            parent = self,
            title = "Load fluidic configuration",
            filetypes = [("Tab-separated values", "*.tsv"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as file:
                rows = [line.rstrip("\n").split("\t") for line in file if line.strip() != ""]
        except OSError as err:
            self._info(f"  Could not load configuration: {err}", error=True)
            return
        # map physical port name -> (rate, volume), skipping the header and malformed rows
        data = {}
        for row in rows:
            if len(row) < 3 or row[0].strip().lower() == "port":
                continue
            data[row[0].strip()] = (row[1].strip(), row[2].strip())
        # clear the sheet, then apply the loaded values so the display matches the file exactly
        applied = 0
        for cell in self.cells:
            if cell.disabled:
                continue
            cell.set("", "")
            if cell.port_name in data:
                cell.set(*data[cell.port_name])
                applied += 1
        self._info(f"  Loaded {applied} port(s) from {path}", error=False)
    # ---------------------------------------------------------------------------------------------
    def _info(self, text, error=True):
        """Function: show a status message under the port grid (red if error, green if not)."""
        self.lbl_inf.configure(text=text, text_color=(PARAMS_ECL if error else PARAMS_OCL))
        self.lbl_inf.grid(row=2, column=0, padx=10, pady=(0,10), sticky="nesw")
    # ---------------------------------------------------------------------------------------------
    @staticmethod
    def _to_int(text):
        """Function: floor(abs()) of a numeric string, or None if blank / not a number."""
        if text == "":
            return None
        try:
            return math.floor(abs(float(text)))
        except (ValueError, TypeError):
            return None
    # ---------------------------------------------------------------------------------------------
    def on_closing(self):
        """Function: enforce quit manually before closing."""
        self.quit()


# ========================================= main function =========================================

def mercury_05():
    """
    Main application loop of mercury 05, return the list of (port, rate, volume) commands.
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
        return []
