"""
Mercury 00: miscellaneous functions, project version 1.25 (with python 3.9).
"""

import os
import tkinter
from tkinter import filedialog

import yaml
import customtkinter
import numpy as np
from PIL import Image, ImageTk, ImageOps, ImageChops

from mercury_01 import open_file_dialog

# from main import PARAMS_DTP
# from main import PARAMS_EXP
# from main import PARAMS_MCI
# from main import PARAMS_MSK
# from main import PARAMS_LSR
# from main import PARAMS_MAP
# from main import PARAMS_PLN
# from main import PARAMS_CRD
# from main import PARAMS_GLB
# from main import PARAMS_SCT
# from main import PARAMS_BIT
# from main import PARAMS_TMP

# ctk window title
WINDOW_TXT = "Mercury 0 - Mask Calibration"
# scan size for laser cleaving
LASER_SIZE = 2.5
# default mask save location
LASER_MASK = "default_mask.png"
# default laser image save location
LASER_SAVE = "default_mask_result.tif"
# default laser mask calibration preset
LASER_PRST = "default_calibration.yaml"


# ===================================== customtkinter classes =====================================

# root class for storing/passing information, parent class of app class
class Root:
    """
    Class: root class of ctk mainloop app, will store and pass saved parameters.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self):
        super().__init__()
        self.rtn = ('', '', '', [], LASER_SIZE)


# app class for ctk window mainloop
class App(customtkinter.CTk, Root):
    """
    Class: app class for main application window and customtkinter main loop.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, x=None, y=None, z=None):
        super().__init__()
        # ---------------------------------- application setting ----------------------------------
        # set window title
        self.title(WINDOW_TXT)
        # set window grid configuation
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        # save passed parameters
        self.init_x = x
        self.init_y = y
        self.init_z = z
        # -------------------------------------- GUI setting --------------------------------------
        # configure control pannels
        self.control_pannels = SeriesEntries(
            master=self,
            initial_values=[self.init_x, self.init_y, self.init_z, LASER_SIZE],
            labels=["Microscope X", "Microscope Y", "Microscope Z", "Laser Scan Size"],
        )
        self.control_pannels.grid(
            row=0, column=0, padx=10, pady=5, sticky="ew", columnspan=3
        )
        # label for mask path input
        self.ctk_label_maskpath = customtkinter.CTkLabel(
            master=self, width=150, height=28, text="Mask File (Full Path):"
        )
        self.ctk_label_maskpath.grid(row=1, column=0, padx=(10,0), pady=(10,5))
        # entry for mask path
        self.ctk_entry_maskpath = customtkinter.CTkEntry(
            master=self, width=400, height=28, textvariable=tkinter.StringVar(
                master=None,
                value=os.path.join(os.path.dirname(os.path.realpath(__file__)), LASER_MASK)
            )
        )
        self.ctk_entry_maskpath.grid(row=1, column=1, padx=5, pady=(10,5))
        self.ctk_button_maskpath = customtkinter.CTkButton(
            master = self,
            width = 28,
            height = 28,
            text = "...",
            command = lambda: self.filedialogue_setpath(self.ctk_entry_maskpath)
        )
        self.ctk_button_maskpath.grid(row=1, column=2, padx=(0,10), pady=(10,5))
        # configure skip button
        self.ctk_button_skip = customtkinter.CTkButton(
            master=self,
            text="Skip Laser Imaging",
            command = self.skip,
            fg_color = "transparent",
            border_width = 1,
            hover_color = "gray23"
        )
        self.ctk_button_skip.grid(
            row=2, column=0, padx=10, pady=(10,0), sticky="ew", columnspan=3
        )
        # configure commence button
        self.ctk_button_commence = customtkinter.CTkButton(
            master=self, height=28, text="Commence", command=self.commence
        )
        self.ctk_button_commence.grid(
            row=3, column=0, padx=10, pady=(5,10), sticky="ew", columnspan=3
        )
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on call ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def filedialogue_setpath(self, ctk_entry:customtkinter.CTkEntry=None):
        """
        Function: use filedialogue to find a filepath, set the provided ctk entry.
        """
        file = open_file_dialog(
            "Select Laser Mask (.png)",
            os.path.dirname(os.path.realpath(__file__)),
            [("Mask Image", "*.png")]
        )
        ctk_entry.configure(textvariable=tkinter.StringVar(master=self,value=file))
    # ---------------------------------------------------------------------------------------------
    def skip(self):
        """
        Function: return default return value, but with laser scan size set to -1.
        """
        self.rtn = ('', '', '', [], -1)
        self.quit()
    # ---------------------------------------------------------------------------------------------
    def commence(self):
        """
        Function: execute the function linked to the selected tab and exit.
        """
        control_panel_rtn = self.control_pannels.get()
        try:
            x = round(float(control_panel_rtn[0]))
        except (ValueError, TypeError):
            ctk_entry_warning(self.control_pannels.entries[0])
            return
        try:
            y = round(float(control_panel_rtn[1]))
        except (ValueError, TypeError):
            ctk_entry_warning(self.control_pannels.entries[1])
            return
        try:
            z = round(float(control_panel_rtn[2]))
        except (ValueError, TypeError):
            ctk_entry_warning(self.control_pannels.entries[2])
            return
        try:
            scan_size = float(control_panel_rtn[3])
        except (ValueError, TypeError):
            ctk_entry_warning(self.control_pannels.entries[3])
            return
        if not os.path.isfile(self.ctk_entry_maskpath.get()):
            ctk_entry_warning(self.ctk_entry_maskpath)
            return
        self.rtn = (
            os.path.dirname(os.path.realpath(__file__)),
            LASER_SAVE,
            self.ctk_entry_maskpath.get(),
            [x, y, z],
            scan_size
        )
        self.quit()
    # ---------------------------------------------------------------------------------------------
    def on_closing(self):
        """
        Function: enforce quit manually before closing.
        """
        self.quit()


class SeriesEntries(customtkinter.CTkFrame):
    """
    Class: ctk frame for parameter entries (label + entry) arranged horizontally in a series.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, master, initial_values, labels=None, widget_pad=5, label_tab=" ", **kwargs):
        super().__init__(master, **kwargs)
        # ------------------------------ initialize frame GUI layout ------------------------------
        # check if labels and initial values are matched up
        has_labels = True
        if labels is not None:
            if len(labels) != len(initial_values):
                raise ValueError("labels and initial_values must have the same length")
        else:
            has_labels = False
            labels = initial_values
        # create, grid, and put entry labels/entries in lists
        self.labels = []
        self.entries = []
        pad = widget_pad
        for i, (label_text, init_val) in enumerate(zip(labels, initial_values)):
            if has_labels is True:
                # label row
                lbl = customtkinter.CTkLabel(
                    self, text=label_tab+str(label_text), anchor="w", justify="left"
                )
                lbl.grid(row=0, column=i, padx=pad if i==0 else (0,pad), pady=(pad, 0), sticky="w")
                self.labels.append(lbl)
            # entry row
            entry = customtkinter.CTkEntry(self)
            entry.grid(row=1, column=i, padx=pad if i == 0 else (0,pad), pady=pad, sticky="we")
            # set initial values
            if init_val is not None:
                entry.insert(0, str(init_val))
            self.entries.append(entry)
        # make columns expand evenly
        for i in range(len(labels)):
            self.grid_columnconfigure(i, weight=1)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on call ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def get(self):
        """Function: return all entry values as a list"""
        return [entry.get() if entry.get() != "" else None for entry in self.entries]
    # ---------------------------------------------------------------------------------------------
    def set(self, index, value):
        """Function: set the value of an entry by index"""
        if not 0 <= index < len(self.entries):
            raise IndexError("Index out of range")
        entry = self.entries[index]
        entry.delete(0, "end")
        if value is not None:
            entry.insert(0, str(value))


# app class for mask calibration interface
class MaskCalibration(customtkinter.CTk):
    """
    Class: customtkinter app for mask calibration (background + foreground overlay).
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(
        self,
        bg_image_path,
        fg_image_path = LASER_MASK,
        preset_path = LASER_PRST,
        image_scaling = 0.5,
        inner_border_size = 10
    ):
        super().__init__()
        # ----------------------------------- define properties -----------------------------------
        # set window property, window is wrapped tightly around the size of the frames
        self.title("Mask Calibration")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        # load and rescale background image (laser image)
        bg = Image.open(bg_image_path)
        bw, bh = bg.size
        bg = bg.resize((round(bw * image_scaling), round(bh * image_scaling)), resample=0)
        bg = convert_to_rgba(bg, alpha=255)
        self.bg_image = bg
        # load and rescale foreground image (laser mask)
        fg = Image.open(fg_image_path)
        fw, fh = fg.size
        fg = fg.resize((round(fw * image_scaling), round(fh * image_scaling)), resample=0)
        fg = convert_to_rgba(fg, alpha=128)
        self.fg_image = fg
        # save image scaling factor for future reference
        self.scaling_factor = image_scaling
        # -------------------------------------- GUI setting --------------------------------------
        # set image display/preview frame
        self.image_display = ImageDisplay(
            master=self,
            fg_img=self.fg_image,
            bg_img=self.bg_image,
            preset=load_mask_preset(preset_path, image_scaling)
        )
        self.image_display.grid(
            row=0, column=0,
            padx=inner_border_size,
            pady=inner_border_size,
            sticky="nse"
        )
        # set up callibration control panel
        self.control_panel = CalibrationControl(
            master=self,
            preset_path=preset_path,
            image_scaling=image_scaling
        )
        self.control_panel.grid(
            row=0, column=1,
            padx=(0, inner_border_size),
            pady=inner_border_size/2,
            sticky="nsw"
        )
        # -------------------------------------- key mapping --------------------------------------
        self.bind_all("<KeyPress>", self.on_key_press)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on call ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def on_key_press(self, event):
        """
        Function: invoke functions when key press is detected.
        """
        # bind to keyboard buttons
        if event.keysym == "w" or event.keysym == "Up":
            self.control_panel.key_w.invoke()
        if event.keysym == "a" or event.keysym == "Left":
            self.control_panel.key_a.invoke()
        if event.keysym == "s" or event.keysym == "Down":
            self.control_panel.key_s.invoke()
        if event.keysym == "d" or event.keysym == "Right":
            self.control_panel.key_d.invoke()
        if event.keysym == "q":
            self.control_panel.key_q.invoke()
        if event.keysym == "e":
            self.control_panel.key_e.invoke()
        if event.keysym == "r":
            self.control_panel.key_r.invoke()
        if event.keysym == "f":
            self.control_panel.key_f.invoke()
        if event.keysym == "v":
            self.control_panel.key_v.invoke()
        # bind to numpad buttons
        if event.keysym == "7":
            self.control_panel.numpadbutton_7.invoke()
        if event.keysym == "8":
            self.control_panel.numpadbutton_8.invoke()
        if event.keysym == "9":
            self.control_panel.numpadbutton_9.invoke()
        if event.keysym == "4":
            self.control_panel.numpadbutton_4.invoke()
        if event.keysym == "5":
            self.control_panel.numpadbutton_5.invoke()
        if event.keysym == "6":
            self.control_panel.numpadbutton_6.invoke()
        if event.keysym == "1":
            self.control_panel.numpadbutton_1.invoke()
        if event.keysym == "2":
            self.control_panel.numpadbutton_2.invoke()
        if event.keysym == "3":
            self.control_panel.numpadbutton_3.invoke()
    # ---------------------------------------------------------------------------------------------
    def on_closing(self):
        """
        Function: enforce quit manually before closing.
        """
        self.quit()


# frame class for mask calibration control
class CalibrationControl(customtkinter.CTkFrame):
    """
    Class: customtkinter frame class for mask calibration control.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(
        self,
        master,
        preset_path,
        image_scaling = 0.5,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        # ---------------------------------- application setting ----------------------------------
        self.current_anchor = "nw"
        self.ccw = True
        self.path = preset_path
        # -------------------------------------- GUI setting --------------------------------------
        # fill column 0 with empty label
        self.label_empty0 = customtkinter.CTkLabel(
            master=self,
            width=10,
            height=10,
            text=" "
        )
        self.label_empty0.grid(row=0, column=0, padx=2, pady=2)
        # fill column 4 with empty label
        self.label_empty4 = customtkinter.CTkLabel(
            master=self,
            width=10,
            height=10,
            text=" "
        )
        self.label_empty4.grid(row=0, column=4, padx=2, pady=2)
        # label the first area
        self.label_area01 = customtkinter.CTkLabel(
            master=self,
            anchor="w",
            text="Movement / Resizing: "
        )
        self.label_area01.grid(row=0, column=1, padx=2, pady=(6,4), columnspan=3, sticky="w")
        # wasd buttons for controlling foreground location
        self.key_w = customtkinter.CTkButton(
            master=self,
            width=60,
            height=60,
            text="▲",
            fg_color="grey23",
            hover_color="gray46",
            command=lambda: self.move_foreground("n")
        )
        self.key_w.grid(row=1, column=2, padx=2, pady=2)
        self.key_a = customtkinter.CTkButton(
            master=self,
            width=60,
            height=60,
            text="◀",
            fg_color="grey23",
            hover_color="gray46",
            command=lambda: self.move_foreground("w")
        )
        self.key_a.grid(row=2, column=1, padx=2, pady=2)
        self.key_s = customtkinter.CTkButton(
            master=self,
            width=60,
            height=60,
            text="▼",
            fg_color="grey23",
            hover_color="gray46",
            command=lambda: self.move_foreground("s")
        )
        self.key_s.grid(row=2, column=2, padx=2, pady=2)
        self.key_d = customtkinter.CTkButton(
            master=self,
            width=60,
            height=60,
            text="▶",
            fg_color="grey23",
            hover_color="gray46",
            command=lambda: self.move_foreground("e")
        )
        self.key_d.grid(row=2, column=3, padx=2, pady=2)
        # qe buttons for resizing
        self.key_q = customtkinter.CTkButton(
            master=self,
            width=60,
            height=60,
            text="-",
            fg_color="grey23",
            hover_color="gray46",
            command=lambda: self.resize_foreground(-2)
        )
        self.key_q.grid(row=1, column=1, padx=2, pady=2)
        self.key_e = customtkinter.CTkButton(
            master=self,
            width=60,
            height=60,
            text="+",
            fg_color="grey23",
            hover_color="gray46",
            command=lambda: self.resize_foreground(2)
        )
        self.key_e.grid(row=1, column=3, padx=2, pady=2)
        # label the second area
        self.label_area02 = customtkinter.CTkLabel(
            master=self,
            anchor="w",
            text="Rotation / Flipping: "
        )
        self.label_area02.grid(row=3, column=1, padx=2, pady=(6,4), columnspan=3, sticky="w")
        # controls for rotation and flipping
        self.key_r = customtkinter.CTkButton(
            master=self,
            width=60,
            height=60,
            text="↻",
            fg_color="grey23",
            hover_color="gray46",
            command=lambda: self.rotate_foreground(90)
        )
        self.key_r.grid(row=4, column=1, padx=2, pady=2)
        self.key_f = customtkinter.CTkButton(
            master=self,
            width=60,
            height=60,
            text="⇔",
            fg_color="grey23",
            hover_color="gray46",
            command=lambda: self.flip_foreground(horizontal=True)
        )
        self.key_f.grid(row=4, column=2, padx=2, pady=2)
        self.key_v= customtkinter.CTkButton(
            master=self,
            width=60,
            height=60,
            text="⇕",
            fg_color="grey23",
            hover_color="gray46",
            command=lambda: self.flip_foreground(vertical=True)
        )
        self.key_v.grid(row=4, column=3, padx=2, pady=2)
        # label the third area
        self.label_area03 = customtkinter.CTkLabel(
            master=self,
            anchor="w",
            text="Vertices Adjustment: "
        )
        self.label_area03.grid(row=5, column=1, padx=2, pady=(6,4), columnspan=3, sticky="w")
        # 7 for selecting top-left corner
        self.numpadbutton_7 = customtkinter.CTkButton(
            master=self,
            width=60,
            height=60,
            text="┏",
            fg_color="grey23",
            hover_color="gray46",
            command=lambda: self.update_anchor("nw")
        )
        self.numpadbutton_7.grid(row=7, column=1, padx=2, pady=2)
        # 8 for moving selected corner up
        self.numpadbutton_8 = customtkinter.CTkButton(
            master=self,
            width=60,
            height=60,
            text="⇧",
            fg_color="grey23",
            hover_color="gray46",
            command=lambda: self.move_anchor("n")
        )
        self.numpadbutton_8.grid(row=7, column=2, padx=2, pady=2)
        # 9 for selecting top-right corner
        self.numpadbutton_9 = customtkinter.CTkButton(
            master=self,
            width=60,
            height=60,
            text="┓",
            fg_color="grey23",
            hover_color="gray46",
            command=lambda: self.update_anchor("ne")
        )
        self.numpadbutton_9.grid(row=7, column=3, padx=2, pady=2)
        # 4 for moving selected corner left
        self.numpadbutton_4 = customtkinter.CTkButton(
            master=self,
            width=60,
            height=60,
            text="⇦",
            fg_color="grey23",
            hover_color="gray46",
            command=lambda: self.move_anchor("w")
        )
        self.numpadbutton_4.grid(row=8, column=1, padx=2, pady=2)
        # 5 for resetting current changes
        self.numpadbutton_5 = customtkinter.CTkButton(
            master=self,
            width=60,
            height=60,
            text="Hide",
            fg_color="grey23",
            hover_color="gray46",
            command=self.master.image_display.toggle_hide
            # command=lambda: self.reset_changes(image_scaling=self.master.scaling_factor)
        )
        self.numpadbutton_5.grid(row=8, column=2, padx=2, pady=2)
        # 6 for moving selected corner right
        self.numpadbutton_6 = customtkinter.CTkButton(
            master=self,
            width=60,
            height=60,
            text="⇨",
            fg_color="grey23",
            hover_color="gray46",
            command=lambda: self.move_anchor("e")
        )
        self.numpadbutton_6.grid(row=8, column=3, padx=2, pady=2)
        # 1 for selecting bottom-left corner
        self.numpadbutton_1 = customtkinter.CTkButton(
            master=self,
            width=60,
            height=60,
            text="┗",
            fg_color="grey23",
            hover_color="gray46",
            command=lambda: self.update_anchor("sw")
        )
        self.numpadbutton_1.grid(row=9, column=1, padx=2, pady=2)
        # 2 for moving selected corner down
        self.numpadbutton_2 = customtkinter.CTkButton(
            master=self,
            width=60,
            height=60,
            text="⇩",
            fg_color="grey23",
            hover_color="gray46",
            command=lambda: self.move_anchor("s")
        )
        self.numpadbutton_2.grid(row=9, column=2, padx=2, pady=2)
        # 3 for selecting bottom-right corner
        self.numpadbutton_3 = customtkinter.CTkButton(
            master=self,
            width=60,
            height=60,
            text="┛",
            fg_color="grey23",
            hover_color="gray46",
            command=lambda: self.update_anchor("se")
        )
        self.numpadbutton_3.grid(row=9, column=3, padx=2, pady=2)\
        # label the fourth area
        self.label_area04 = customtkinter.CTkLabel(
            master=self,
            anchor="w",
            text="Foreground / Background: "
        )
        self.label_area04.grid(row=10, column=1, padx=2, pady=(6,4), columnspan=3, sticky="w")
        # buttons for inverting/changing foreground/background
        self.button_in_foreground = customtkinter.CTkButton(
            master=self,
            text="Invert Foreground",
            command=self.invert_foreground,
            fg_color="transparent",
            border_width=1,
            hover_color="gray23"
        )
        self.button_in_foreground.grid(row=11, column=1, padx=2, pady=2, columnspan=3, sticky="ew")
        self.button_ch_foreground = customtkinter.CTkButton(
            master=self,
            text="Load Foreground",
            command=lambda: self.change_foreground(image_scaling=image_scaling),
            fg_color="transparent",
            border_width=1,
            hover_color="gray23"
        )
        self.button_ch_foreground.grid(row=12, column=1, padx=2, pady=2, columnspan=3, sticky="ew")
        self.button_ch_background = customtkinter.CTkButton(
            master=self,
            text="Load Background",
            command=lambda: self.change_background(image_scaling=image_scaling),
            fg_color="transparent",
            border_width=1,
            hover_color="gray23"
        )
        self.button_ch_background.grid(row=13, column=1, padx=2, pady=2, columnspan=3, sticky="ew")
        self.button_reset = customtkinter.CTkButton(
            master=self,
            text="Reset Adjustments",
            command=self.reset_changes,
            fg_color="transparent",
            border_width=1,
            hover_color="gray23"
        )
        self.button_reset.grid(row=14, column=1, padx=2, pady=2, columnspan=3, sticky="ew")
        # label the fifth area
        self.label_area05 = customtkinter.CTkLabel(
            master=self,
            anchor="w",
            text="Load / Save Options: "
        )
        self.label_area05.grid(row=15, column=1, padx=2, pady=(6,4), columnspan=3, sticky="w")
        # buttons for loading and saving mask presets
        self.load_button = customtkinter.CTkButton(
            master=self,
            text="Load Preset",
            command=lambda: self.load_preset(scaling_factor=image_scaling),
            fg_color="transparent",
            border_width=1,
            hover_color="gray23"
        )
        self.load_button.grid(row=16, column=1, padx=2, pady=2, columnspan=3, sticky="ew")
        self.save_button = customtkinter.CTkButton(
            master=self,
            text="Save Preset",
            command=lambda: self.save_preset(image_scaling=image_scaling)
        )
        self.save_button.grid(row=17, column=1, padx=2, pady=2, columnspan=3, sticky="ew")
        # update initial anchor setting
        self.update_anchor(self.current_anchor)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on call ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def reset_changes(self, image_scaling=0.5):
        """
        Function: reset foreground to the currently loaded preset.
        """
        rotation, vertical, horizontal, x, y, w, h = load_mask_preset(self.path, image_scaling)
        self.master.image_display.rotation = rotation
        self.master.image_display.vertical = vertical
        self.master.image_display.horizontal = horizontal
        self.master.image_display.x = x
        self.master.image_display.y = y
        self.master.image_display.w = w
        self.master.image_display.h = h
        self.master.image_display.apply_preset()
    # ---------------------------------------------------------------------------------------------
    def load_preset(self, scaling_factor=0.5):
        """
        Function: open file dialogue window, load mask calibration preset.
        """
        try:
            path = open_file_dialog(
                "Select a preset file",
                os.path.join(os.path.expanduser("~"), "Desktop"),
                [("Mask Calibration Preset", "*.yaml *.yml")]
            )
            if path is None or '':
                raise FileNotFoundError(f"Warning: invalid file path {path}")
        except FileNotFoundError as e:
            print(f"Warning: cannot open preset: {e}.")
        try:
            rotation, vertical, horizontal, x, y, w, h = load_mask_preset(self.path,scaling_factor)
            self.master.image_display.rotation = rotation
            self.master.image_display.vertical = vertical
            self.master.image_display.horizontal = horizontal
            self.master.image_display.x = x
            self.master.image_display.y = y
            self.master.image_display.w = w
            self.master.image_display.h = h
            self.master.image_display.apply_preset()
            self.path = path
        except (ValueError, TypeError, RuntimeError, FileNotFoundError) as e:
            print(f"Warning: unable to load preset at {path}: {e}")
    # ---------------------------------------------------------------------------------------------
    def save_preset(self, image_scaling=0.5):
        """
        Function: open file dialogue window, save mask calibration preset.
        """
        path = filedialog.asksaveasfilename(
            title="Save preset as file",
            defaultextension="*.yaml",
            initialdir=os.path.join(os.path.expanduser("~"), "Desktop"),
            filetypes=[("Mask Calibration Preset", "*.yaml *.yml")]
        )
        if path != '':
            try:
                # if file already exists, overwrite; otherwise, save as new
                with open(path, 'r+' if os.path.exists(path) else 'w', encoding="utf-8") as file:
                    data = {
                        'rotation': self.master.image_display.rotation,
                        'flip_vertical': self.master.image_display.vertical,
                        'flip_horizontal': self.master.image_display.horizontal,
                        'x': self.master.image_display.x / image_scaling,
                        'y': self.master.image_display.y / image_scaling,
                        'w': self.master.image_display.w / image_scaling,
                        'h': self.master.image_display.h / image_scaling,
                    }
                    yaml.dump(data, file, default_flow_style=False, sort_keys=False)
            except (ValueError, TypeError, RuntimeError) as e:
                print(f"Warning: unable to save preset at {path}: {e}")
            # # for older txt-based preset files
            # try:
            #     if os.path.exists(path):
            #         existing = open(path, 'r+', encoding="utf-8").readlines()
            #     file = open(path, 'w', encoding="utf-8")
            #     file.write(f"{self.master.image_display.rotation}\n")
            #     file.write(f"{int(self.master.image_display.vertical)}\n")
            #     file.write(f"{int(self.master.image_display.horizontal)}\n")
            #     file.write(f"{int(self.master.image_display.x / image_scaling)}\n")
            #     file.write(f"{int(self.master.image_display.y / image_scaling)}\n")
            #     file.write(f"{int(self.master.image_display.w / image_scaling)}\n")
            #     file.write(f"{int(self.master.image_display.h / image_scaling)}\n")
            #     file.close()
            # except (ValueError, TypeError, RuntimeError) as e:
            #     if existing is not None:
            #         file = open(path, 'w', encoding="utf-8")
            #         file.writelines(existing)
            #         file.close()
            #     print(f"Warning: unable to save preset at {path}: {e}")
    # ---------------------------------------------------------------------------------------------
    def change_foreground(self, image_scaling=1):
        """
        Function: open file dialogue window, change foreground to the designated image.
        """
        try:
            path = open_file_dialog(
                "Select foreground",
                os.path.join(os.path.expanduser("~"), "Desktop"),
                [("Mask Image", "*.png")]
            )
        except FileNotFoundError as e:
            print(f"Warning: cannot open image: {e}.")
        if path != '':
            fg = Image.open(path)
            fw, fh = fg.size
            fg = fg.resize((round(fw * image_scaling), round(fh * image_scaling)), resample=0)
            fg = convert_to_rgba(fg, alpha=128)
            self.master.fg_image = fg
            self.master.image_display.foreground_original = fg
            self.master.image_display.foreground_image = fg.copy()
            self.master.image_display.apply_preset()
    # ---------------------------------------------------------------------------------------------
    def change_background(self, image_scaling):
        """
        Function: open file dialogue window, change background to the designated image.
        """
        try:
            path = open_file_dialog(
                "Select background",
                os.path.join(os.path.expanduser("~"), "Desktop"),
                [("Laser Image", "*.tif *.tiff")]
            )
        except FileNotFoundError as e:
            print(f"Warning: cannot open image: {e}.")
        if path != '':
            bg = Image.open(path)
            bw, bh = bg.size
            bg = bg.resize((round(bw * image_scaling), round(bh * image_scaling)), resample=0)
            bg = convert_to_rgba(bg, alpha=255)
            self.master.bg_image = bg
            self.master.image_display.background_image = bg
            self.master.image_display.bg_tk = ImageTk.PhotoImage(bg)
            self.master.image_display.canvas.itemconfig(
                self.master.image_display.bg_item, image=self.master.image_display.bg_tk
            )
            self.master.image_display.canvas.coords(
                self.master.image_display.bg_item, 0, 0)
    # ---------------------------------------------------------------------------------------------
    def invert_foreground(self):
        """
        Function: update foreground image as an inverted image of itself.
        """
        self.master.fg_image = ImageChops.invert(self.master.fg_image)
        self.master.image_display.foreground_original = ImageChops.invert(
            self.master.image_display.foreground_original
        )
        self.master.image_display.foreground_image = ImageChops.invert(
            self.master.image_display.foreground_image
        )
        self.master.image_display.apply_preset()
    # ---------------------------------------------------------------------------------------------
    def update_anchor(self, anchor):
        """
        Function: update anchor location and disable corresponding numpad button.
        """
        if anchor == "nw":
            # update disabled button
            self.numpadbutton_1.configure(state="normal", fg_color="grey23")
            self.numpadbutton_3.configure(state="normal", fg_color="grey23")
            self.numpadbutton_7.configure(state="disabled", fg_color="#14375e")
            self.numpadbutton_9.configure(state="normal", fg_color="grey23")
            # update selected anchor
            self.current_anchor = anchor
        elif anchor == "ne":
            # update disabled button
            self.numpadbutton_1.configure(state="normal", fg_color="grey23")
            self.numpadbutton_3.configure(state="normal", fg_color="grey23")
            self.numpadbutton_7.configure(state="normal", fg_color="grey23")
            self.numpadbutton_9.configure(state="disabled", fg_color="#14375e")
            # update selected anchor
            self.current_anchor = anchor
        elif anchor == "sw":
            # update disabled button
            self.numpadbutton_1.configure(state="disabled", fg_color="#14375e")
            self.numpadbutton_3.configure(state="normal", fg_color="grey23")
            self.numpadbutton_7.configure(state="normal", fg_color="grey23")
            self.numpadbutton_9.configure(state="normal", fg_color="grey23")
            # update selected anchor
            self.current_anchor = anchor
        elif anchor == "se":
            # update disabled button
            self.numpadbutton_1.configure(state="normal", fg_color="grey23")
            self.numpadbutton_3.configure(state="disabled", fg_color="#14375e")
            self.numpadbutton_7.configure(state="normal", fg_color="grey23")
            self.numpadbutton_9.configure(state="normal", fg_color="grey23")
            # update selected anchor
            self.current_anchor = anchor
    # ---------------------------------------------------------------------------------------------
    def move_anchor(self, direction, distance=2, anchor=None):
        """
        Function: move the current anchor in cardinal direction, update foreground.
        """
        # if anchor is not given, use the current anchor
        if anchor is None:
            anchor = self.current_anchor
        # depending on which anchor is selected, update foreground location and size.
        if anchor == "nw":
            if direction == "n":
                self.master.image_display.y -= distance
                self.master.image_display.h += distance
                self.numpadbutton_8.configure(fg_color="#14375e")
                self.after(100, lambda: self.numpadbutton_8.configure(fg_color="grey23"))
            if direction == "s":
                self.master.image_display.y += distance
                self.master.image_display.h -= distance
                self.numpadbutton_2.configure(fg_color="#14375e")
                self.after(100, lambda: self.numpadbutton_2.configure(fg_color="grey23"))
            if direction == "e":
                self.master.image_display.x += distance
                self.master.image_display.w -= distance
                self.numpadbutton_6.configure(fg_color="#14375e")
                self.after(100, lambda: self.numpadbutton_6.configure(fg_color="grey23"))
            if direction == "w":
                self.master.image_display.x -= distance
                self.master.image_display.w += distance
                self.numpadbutton_4.configure(fg_color="#14375e")
                self.after(100, lambda: self.numpadbutton_4.configure(fg_color="grey23"))
            self.master.image_display.apply_preset()
        elif anchor == "ne":
            if direction == "n":
                self.master.image_display.y -= distance
                self.master.image_display.h += distance
                self.numpadbutton_8.configure(fg_color="#14375e")
                self.after(100, lambda: self.numpadbutton_8.configure(fg_color="grey23"))
            if direction == "s":
                self.master.image_display.y += distance
                self.master.image_display.h -= distance
                self.numpadbutton_2.configure(fg_color="#14375e")
                self.after(100, lambda: self.numpadbutton_2.configure(fg_color="grey23"))
            if direction == "e":
                self.master.image_display.w += distance
                self.numpadbutton_6.configure(fg_color="#14375e")
                self.after(100, lambda: self.numpadbutton_6.configure(fg_color="grey23"))
            if direction == "w":
                self.master.image_display.w -= distance
                self.numpadbutton_4.configure(fg_color="#14375e")
                self.after(100, lambda: self.numpadbutton_4.configure(fg_color="grey23"))
            self.master.image_display.apply_preset()
        elif anchor == "sw":
            if direction == "n":
                self.master.image_display.h -= distance
                self.numpadbutton_8.configure(fg_color="#14375e")
                self.after(100, lambda: self.numpadbutton_8.configure(fg_color="grey23"))
            if direction == "s":
                self.master.image_display.h += distance
                self.numpadbutton_2.configure(fg_color="#14375e")
                self.after(100, lambda: self.numpadbutton_2.configure(fg_color="grey23"))
            if direction == "e":
                self.master.image_display.x += distance
                self.master.image_display.w -= distance
                self.numpadbutton_6.configure(fg_color="#14375e")
                self.after(100, lambda: self.numpadbutton_6.configure(fg_color="grey23"))
            if direction == "w":
                self.master.image_display.x -= distance
                self.master.image_display.w += distance
                self.numpadbutton_4.configure(fg_color="#14375e")
                self.after(100, lambda: self.numpadbutton_4.configure(fg_color="grey23"))
            self.master.image_display.apply_preset()
        elif anchor == "se":
            if direction == "n":
                self.master.image_display.h -= distance
                self.numpadbutton_8.configure(fg_color="#14375e")
                self.after(100, lambda: self.numpadbutton_8.configure(fg_color="grey23"))
            if direction == "s":
                self.master.image_display.h += distance
                self.numpadbutton_2.configure(fg_color="#14375e")
                self.after(100, lambda: self.numpadbutton_2.configure(fg_color="grey23"))
            if direction == "e":
                self.master.image_display.w += distance
                self.numpadbutton_6.configure(fg_color="#14375e")
                self.after(100, lambda: self.numpadbutton_6.configure(fg_color="grey23"))
            if direction == "w":
                self.master.image_display.w -= distance
                self.numpadbutton_4.configure(fg_color="#14375e")
                self.after(100, lambda: self.numpadbutton_4.configure(fg_color="grey23"))
            self.master.image_display.apply_preset()
    # ---------------------------------------------------------------------------------------------
    def move_foreground(self, direction, distance=2):
        """
        Function: move the entire foreground towards a given direction (n/s/e/w).
        """
        # select direction to move, update variables, change button appearance, and update.
        if direction == "n":
            self.master.image_display.y -= distance
            self.key_w.configure(fg_color="#14375e")
            self.after(100, lambda: self.key_w.configure(fg_color="grey23"))
        if direction == "s":
            self.master.image_display.y += distance
            self.key_s.configure(fg_color="#14375e")
            self.after(100, lambda: self.key_s.configure(fg_color="grey23"))
        if direction == "e":
            self.master.image_display.x += distance
            self.key_d.configure(fg_color="#14375e")
            self.after(100, lambda: self.key_d.configure(fg_color="grey23"))
        if direction == "w":
            self.master.image_display.x -= distance
            self.key_a.configure(fg_color="#14375e")
            self.after(100, lambda: self.key_a.configure(fg_color="grey23"))
        self.master.image_display.apply_preset()
    # ---------------------------------------------------------------------------------------------
    def rotate_foreground(self, degree):
        """
        Function: rotate forground element counter-clockwise, update rotation degree.
        """
        # update rotation degree variable
        r = self.master.image_display.rotation
        r = (r + degree) % 360
        self.master.image_display.rotation = r
        # change button appearences
        self.key_r.configure(fg_color="#14375e")
        self.after(100, lambda: self.key_r.configure(fg_color="grey23"))
        # update foreground element
        self.master.image_display.apply_preset()
    # ---------------------------------------------------------------------------------------------
    def flip_foreground(self, vertical=False, horizontal=False):
        """
        Function: flip foreground element based on input parameter.
        """
        # update flipping state
        if vertical:
            self.master.image_display.vertical = not self.master.image_display.vertical
            self.key_v.configure(fg_color="#14375e")
            self.after(100, lambda: self.key_v.configure(fg_color="grey23"))
        if horizontal:
            self.master.image_display.horizontal = not self.master.image_display.horizontal
            self.key_f.configure(fg_color="#14375e")
            self.after(100, lambda: self.key_f.configure(fg_color="grey23"))
        # update foreground element
        self.master.image_display.apply_preset()
    # ---------------------------------------------------------------------------------------------
    def resize_foreground(self, magnitude=2):
        """
        Function: resize foreground image.
        """
        # check if adding on magnitude would cause zero width/height
        if (self.master.image_display.w + magnitude*2) <= 0:
            print("Warning: cannot set foreground width to 0.")
            return
        if (self.master.image_display.h + magnitude*2) <= 0:
            print("Warning: cannot set foreground height to 0.")
            return
        # apply added-on magnitudes
        self.master.image_display.x -= magnitude
        self.master.image_display.y -= magnitude
        self.master.image_display.w += magnitude*2
        self.master.image_display.h += magnitude*2
        # change button appearences
        if magnitude < 0:
            self.key_q.configure(fg_color="#14375e")
            self.after(100, lambda: self.key_q.configure(fg_color="grey23"))
        if magnitude > 0:
            self.key_e.configure(fg_color="#14375e")
            self.after(100, lambda: self.key_e.configure(fg_color="grey23"))
        # update foreground element
        self.master.image_display.apply_preset()


# ====================================== tkinter app classes ======================================

# frame class for image overlay and display
class ImageDisplay(tkinter.Frame):
    """
    Class: legacy tkinter frame class, overlaying 2 images as tkimages onto a canvas.
    fg_image and bg_image are pil images, both adjusted for size and transparency.
    to control the margin of image display, adjust for frame width and height.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, master, fg_img: Image.Image, bg_img: Image.Image, preset = None, **kwargs):
        super().__init__(master, **kwargs)
        # ---------------------------------- application setting ----------------------------------
        # store states of rotation/flipping/hiding
        self.rotation = 0
        self.vertical = False
        self.horizontal = False
        self.hidden = False
        # store background and foreground images, keep a copy of the original foreground image
        self.background_image = bg_img
        self.foreground_original = fg_img
        self.foreground_image = fg_img.copy()
        # set background and foreground sizes
        bg_width, bg_height = self.background_image.size
        fg_width, fg_height = self.foreground_original.size
        # configure the frame to be the size of the background, disable frame auto-propagation
        self.configure(width=bg_width, height=bg_height)
        self.grid_propagate(False)
        # check foreground size (foreground must be smaller than the background in all dimensions)
        if bg_width < fg_width or bg_height < fg_height:
            raise ValueError(
                f"Foreground ({fg_width}x{fg_height}) exceeds background ({bg_width}x{bg_height})"
            )
        # initialize displacement/size parameters for the foreground
        self.x = 0
        self.y = 0
        self.w = fg_width
        self.h = fg_height
        # try unpacking the preset if provided: (r, v, h, x, y, w, h)
        if preset is not None:
            try:
                if not preset:
                    raise RuntimeError("Independent function `load_preset` failed to load preset.")
                (
                    self.rotation, # int, degrees rotated (ccw)
                    self.vertical, # bool, vertical flipping
                    self.horizontal, # bool, horizontal flipping
                    self.x, # int, pixel coordinate for top-left corner
                    self.y, # int, pixel coordinate for top-left corner
                    self.w, # int, pixel width of the image
                    self.h  # int, pixel height of the image
                ) = preset
            except (ValueError, TypeError, RuntimeError) as e:
                print(f"Warning: unable to apply provided preset: {e}")
        # -------------------------------------- GUI setting --------------------------------------
        # set up tkinter canvas (which will contain both foreground and background photoimages)
        self.canvas = tkinter.Canvas(self, width=bg_width, height=bg_height, highlightthickness=0)
        self.canvas.place(x=0, y=0)
        # set up background photoimage
        self.bg_tk = ImageTk.PhotoImage(self.background_image)
        self.bg_item = self.canvas.create_image(0, 0, image=self.bg_tk, anchor="nw")
        # set up foreground photoimage
        self.fg_tk = ImageTk.PhotoImage(self.foreground_image)
        self.fg_item = self.canvas.create_image(self.x, self.y, image=self.fg_tk, anchor="nw")
        # set up indicator for foreground border
        self.bd_item = self.canvas.create_rectangle(
            self.x, self.y, self.x+self.w, self.y+self.h, outline="#3a7ebf", width=3
        )
        # apply current foreground configuration
        self.apply_preset()
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on call ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def apply_preset(self):
        """
        Function: apply rotation/flipping/resizing and place the foreground at (x,y).
        """
        # read image from saved original copy
        img = self.foreground_original.copy()
        # if needed, rotate and flip the image before ajusting size/transformation
        if self.rotation % 360:
            img = img.rotate(self.rotation, expand=False)
        if self.vertical:
            img = ImageOps.flip(img)
        if self.horizontal:
            img = ImageOps.mirror(img)
        # adjust image size to fit the foreground width and height
        if (img.width, img.height) != (self.w, self.h):
            # resample is set to 0 (nearest) to ensure sharp image
            img = img.resize((self.w, self.h), resample=0)
        # update saved foreground image variable
        self.foreground_image = img
        # create a new photoimage for the modified image
        self.fg_tk = ImageTk.PhotoImage(self.foreground_image)
        # reconfigure foreground photoimage to show modified image
        self.canvas.itemconfig(self.fg_item, image=self.fg_tk)
        # reconfigure foreground photoimage's xy coordinates
        self.canvas.coords(self.fg_item, self.x, self.y)
        # reconfigure border rectangle with new locations and size
        self.canvas.coords(self.bd_item, self.x, self.y, self.x+self.w, self.y+self.h)
    # ---------------------------------------------------------------------------------------------
    def toggle_hide(self):
        """
        Function: hide/unhide foreground element.
        """
        if self.hidden:
            self.canvas.itemconfig(self.fg_item, state="normal")
            self.hidden = False
            self.master.control_panel.numpadbutton_5.configure(
                text="Hide",
                fg_color="grey23"
            )
        else:
            self.canvas.itemconfig(self.fg_item, state="hidden")
            self.hidden = True
            self.master.control_panel.numpadbutton_5.configure(
                text="Unhide",
                fg_color="#14375e"
            )


# ===================================== independent functions =====================================

def mask_calibration(laser_image_path):
    """
    Function: independent function for mask calibration, has no return value and uses ctk mainloop.
    """
    # set customtkinter appearance mode and color theme
    customtkinter.set_appearance_mode("dark")
    customtkinter.set_default_color_theme("blue")
    # enter main loop and return user inputs when ended
    app_01 = MaskCalibration(laser_image_path)
    app_01.resizable(False, False)
    app_01.protocol("WM_DELETE_WINDOW", app_01.on_closing)
    # force the window to lock into focus before disabling the lock
    # app_01.iconify()
    # app_01.update()
    # app_01.deiconify()
    app_01.attributes("-topmost", True)
    app_01.after_idle(app_01.attributes, "-topmost", False)
    app_01.after(10, app_01.focus)
    # enter mainloop (will happen before executing the after script)
    app_01.mainloop()


def convert_to_rgba(img: Image.Image, alpha: int = 255) -> Image.Image:
    """Function: convert any 16-bit/float PIL image to RGBA, set alpha value."""
    # normalize 16-bit image to 8-bit L mode png
    if img.mode in ("I;16", "I;16L", "I;16B", "I"):
        arr = np.array(img, dtype=np.uint16)
        mm = arr.max()
        mn = arr.min()
        if mm == mn:
            arr8 = np.zeros_like(arr, dtype=np.uint8)
        else:
            arr8 = ((arr - mn) / (mm - mn) * 255.0).astype(np.uint8)
        img = Image.fromarray(arr8, mode="L")
    # normalize float image to 8-bit L mode png
    elif img.mode == "F":
        arr = np.array(img, dtype=np.float32)
        amax = float(np.nanmax(arr))
        amin = float(np.nanmin(arr))
        if amax == amin:
            arr8 = np.zeros(arr.shape, dtype=np.uint8)
        else:
            arr = (arr - amin) / (amax - amin)
            arr = np.clip(arr * 255.0, 0, 255).astype(np.uint8)
            arr8 = arr
        img = Image.fromarray(arr8, mode="L")
    # convert resulting image into rgba, set alpha value (max 255)
    img = img.convert("RGBA")
    img.putalpha(alpha)
    return img


def load_mask_preset(file_path, scaling_factor):
    """
    Function: load preset from yaml/yml, adjust for scaling factor. Return false if failed.
    """
    try:
        with open(file_path, 'r+', encoding="utf-8") as file:
            data = yaml.safe_load(file)
            rotation = int(data['rotation'])
            vertical = bool(data['flip_vertical'])
            horizontal = bool(data['flip_horizontal'])
            x = round(float(data['x'])*scaling_factor)
            y = round(float(data['y'])*scaling_factor)
            w = round(float(data['w'])*scaling_factor)
            h = round(float(data['h'])*scaling_factor)
    except (ValueError, TypeError, RuntimeError) as e:
        print(f"Warning: unable to load preset at {file_path}: {e}")
        return False
    return (rotation, vertical, horizontal, x, y, w, h)
    # # for older txt-based preset files
    # try:
    #     file = open(file_path, 'r+', encoding="utf-8").readlines()
    #     rotation = int(file[0])
    #     vertical = False if file[1] == "0\n" else True
    #     horizontal = False if file[2] == "0\n" else True
    #     x = round(int(file[3])*scaling_factor)
    #     y = round(int(file[4])*scaling_factor)
    #     w = round(int(file[5])*scaling_factor)
    #     h = round(int(file[6])*scaling_factor)
    # except (ValueError, TypeError, RuntimeError) as e:
    #     print(f"Warning: unable to load preset at {file_path}: {e}")
    #     return False
    # return (rotation, vertical, horizontal, x, y, w, h)


def ctk_entry_warning(entry: customtkinter.CTkEntry, color="brown", duration=50):
    """
    Function: briefly set designated ctk entry's foreground to a specific color.
    """
    # get original color
    original_color = entry.cget("fg_color")
    # set entry foreground color
    entry.configure(fg_color=color)
    # set entry foreground color to original
    entry.after(duration, lambda: entry.configure(fg_color=original_color))


# ========================================= main function =========================================

def mercury_00(
        init_x = None,
        init_y = None,
        init_z = None
):
    """
    Function: main function with ctk mainloop, returns command index and command string on close.
    """
    # set customtkinter appearance mode and color theme
    customtkinter.set_appearance_mode("dark")
    customtkinter.set_default_color_theme("blue")
    # enter main loop and return user inputs when ended
    app_main = App(init_x, init_y, init_z)
    app_main.resizable(False, False)
    app_main.protocol("WM_DELETE_WINDOW", app_main.on_closing)
    app_main.mainloop()
    try:
        return app_main.rtn
    except AttributeError:
        return ('', '', '', [], LASER_SIZE)

if __name__ == "__main__":
    print(mask_calibration(LASER_SAVE))
