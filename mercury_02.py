"""
Mercury 02: laser scheme constructor, project version 1.2 (with python 3.9).
"""

import os
import shutil
import tkinter
import threading
import customtkinter
from cellpose import models, io
from PIL import Image, ImageChops

WINDOW_TXT = "Mercury II - Laser Scheme Constructor"
WINDOW_RES = "900x600"
PARAMS_DTP = os.path.join(os.path.expanduser("~"), "Desktop")       # desktop folder path
PARAMS_DFT = os.path.join(PARAMS_DTP, "_latest")                    # default folder path
PARAMS_PRV = os.path.join(                                          # resolution previews
    os.path.dirname(os.path.abspath(__file__)),
    "Resolution Preview.png"
)
PARAMS_CRP = (2304, 1728, 192, 384)                                 # resolution of masks
           # (max, init, step, min)
PARAMS_MOD = ["cyto3", "cyto2", "cyto", "nuclei"]                   # cellpose model type
PARAMS_CPD = 40                                                     # cell pixel diameter
PARAMS_CNL = ["Gray", "Red", "Green", "Blue"]                       # channels to segment
PARAMS_EXT = "_cp_mask"                                             # mask name extension
PARAMS_FOV = [1906,2270]                                            # laser coverage size
PARAMS_MSK = [1024,1024]                                            # set mask size limit


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
        self.wdw_top = None
        # -------------------------------------- GUI setting --------------------------------------
        # create file path entry and label
        self.frm_fpe = Fpe(master=self)
        self.frm_fpe.grid(row=0, column=0, padx=10, pady=5, sticky="nesw", columnspan=2)
        # create image preview and control
        self.img_prv = customtkinter.CTkImage(dark_image=Image.open(PARAMS_PRV), size=(325,245))
        self.btn_img = customtkinter.CTkButton(
            master = self,
            fg_color = "transparent",
            text = "",
            image = self.img_prv,
            state = "disabled"
        )
        self.btn_img.grid(row=1, column=0, padx=(20,0), pady=5, sticky="nesw")
        self.frm_img = Img(master=self)
        self.frm_img.grid(row=1, column=1, padx=10, pady=5, sticky="nesw")
        # set cellpose control panel frame
        self.frm_cp2 = Cp2(master=self)
        self.frm_cp2.grid(row=2, column=0, padx=10, pady=5, sticky="nesw", columnspan=2)
        # set preview and commence buttons
        self.btn_cmc = customtkinter.CTkButton(master=self, text="Commence", command=self.app_exp)
        self.btn_cmc.grid(row=3, column=0, padx=10, pady=(5,10), sticky="nesw", columnspan=2)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on call ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def app_exp(self):
        """
        Function: commence operation under current user inputs.
        """
        # set the input frames to disabled
        self.frm_fpe.ent_inp.configure(state="disabled")
        self.frm_fpe.ent_out.configure(state="disabled")
        self.frm_fpe.ent_ext.configure(state="disabled")
        self.frm_fpe.btn_rtn.configure(state="disabled")
        self.frm_img.inp_crx.configure(state="disabled")
        self.frm_img.inp_cry.configure(state="disabled")
        self.frm_img.frm_sld.sld_inp.configure(state="disabled")
        self.frm_img.frm_rdm.btn_rvs.configure(state="disabled")
        self.frm_cp2.inp_mdl.configure(state="disabled")
        self.frm_cp2.inp_dim.configure(state="disabled")
        self.frm_cp2.inp_sgm.configure(state="disabled")
        self.btn_cmc.configure(state="disabled")
        # open a separate top level window
        if self.wdw_top is None or not self.wdw_top.winfo_exists():
            self.wdw_top = Top(self)
        else:
            self.wdw_top.focus()
        self.wdw_top.after(10, self.wdw_top.lift)
        # run export command on new thread
        threading.Thread(target=self.app_cmc).start()
    # ---------------------------------------------------------------------------------------------
    def app_cmc(self):
        """
        Function: commence cp2 mask generation on a new thread.
        """
        # get input and store as variables
        input_folder = self.frm_fpe.ent_inp.get()
        output_folder = self.frm_fpe.ent_out.get()
        name_extension = self.frm_fpe.ent_ext.get()
        mask_cropping = [int(self.frm_img.inp_crx.get()), int(self.frm_img.inp_cry.get())]
        if self.frm_img.frm_rdm.btn_rvs.get() == "Normal":
            reverse_color = False
        else:
            reverse_color = True
        cp2_model_type = self.frm_cp2.inp_mdl.get()
        cell_diameter = self.frm_cp2.inp_dim.get()
        seg_channels = self.frm_cp2.inp_sgm.get()
        # switch case is not compatable with python v3.9
        if seg_channels == "Gray":
            seg_channels = [0,0]
        elif seg_channels == "Red":
            seg_channels = [1,1]
        elif seg_channels == "Green":
            seg_channels = [2,2]
        elif seg_channels == "Blue":
            seg_channels = [3,3]
        try:
            cell_diameter = int(cell_diameter)
        except ValueError:
            cell_diameter = 30
        # gather entry and copy file paths
        if input_folder != output_folder:
            try:
                shutil.copytree(input_folder, output_folder)
            except FileExistsError:
                shutil.copy2(input_folder, output_folder)
        # create cell masks for all images
        inp = []
        out = []
        with os.scandir(output_folder) as entries:
            for entry in entries:
                if entry.is_dir():
                    for file in os.listdir(entry):
                        inp.append(os.path.join(output_folder, entry, file))
                        out.append(
                            os.path.join(
                                output_folder,
                                entry,
                                os.path.splitext(file)[0]
                            ) + name_extension + ".png"
                        )
        for i, o in enumerate(out):
            self.wdw_top.pgb_prg.set((i)/len(out))
            self.wdw_top.lbl_txt.configure(text=f"Constructing Laser Mask: {i}/{len(out)}")
            self.wdw_top.title(f"Export Progress: {i}/{len(out)}")
            create_cpmask_single(
                original = inp[i],
                exported = o,
                cropsize = mask_cropping,
                reversal = reverse_color,
                cp2model = cp2_model_type,
                diameter = cell_diameter,
                channels = seg_channels
            )
        self.quit()


class Fpe(customtkinter.CTkFrame):
    """
    Class: ctk frame for file path entry and image save inputs.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        # -------------------------------------- GUI setting --------------------------------------
        # create label as the frame header
        self.lbl_frm = customtkinter.CTkLabel(
            master = self,
            width = 870,
            text = "File Paths",
            corner_radius = 5,
            fg_color = "grey23"
        )
        self.lbl_frm.grid(row=0, column=0, padx=5, pady=5, sticky="nesw", columnspan=2)
        # create file path entry and label
        self.lbl_inp = customtkinter.CTkLabel(
            master = self,
            text = "Input Folder:"
        )
        self.lbl_inp.grid(row=1, column=0, padx=0, pady=5, sticky="nsew")
        self.ent_inp = customtkinter.CTkEntry(
            master = self,
            width = 700,
            textvariable = tkinter.StringVar(master=self, value=PARAMS_DFT)
        )
        self.ent_inp.grid(row=1, column=1, padx=(0,10), pady=5, sticky="nsew")
        self.lbl_out = customtkinter.CTkLabel(
            master = self,
            text = "Output Folder:"
        )
        self.lbl_out.grid(row=2, column=0, padx=0, pady=5, sticky="nsew")
        self.ent_out = customtkinter.CTkEntry(
            master = self,
            width = 700,
            textvariable = tkinter.StringVar(master=self, value=PARAMS_DFT)
        )
        self.ent_out.grid(row=2, column=1, padx=(0,10), pady=5, sticky="nsew")
        self.lbl_ext = customtkinter.CTkLabel(
            master = self,
            text = "Mask Tail Name:"
        )
        self.lbl_ext.grid(row=3, column=0, padx=0, pady=5, sticky="nsew")
        self.ent_ext = customtkinter.CTkEntry(
            master = self,
            width = 700,
            textvariable = tkinter.StringVar(master=self, value=PARAMS_EXT)
        )
        self.ent_ext.grid(row=3, column=1, padx=(0,10), pady=5, sticky="nsew")
        # create return to default options
        self.btn_rtn = customtkinter.CTkButton(
            master = self,
            text = "Reset Paths to Default",
            fg_color = "transparent",
            border_width = 1,
            hover_color = "#565B5E",
            command = self.fpe_rst
        )
        self.btn_rtn.grid(row=4, column=0, padx=10, pady=5, sticky="nesw", columnspan=2)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on call ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def fpe_rst(self):
        """
        Function: replace file path inputs with default values.
        """
        self.ent_inp.configure(textvariable=tkinter.StringVar(master=self, value=PARAMS_DFT))
        self.ent_out.configure(textvariable=tkinter.StringVar(master=self, value=PARAMS_DFT))


class Img(customtkinter.CTkFrame):
    """
    Class: ctk frame for image resolution/aspect ratio control.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        # -------------------------------------- GUI setting --------------------------------------
        # create label as the frame header
        self.lbl_frm = customtkinter.CTkLabel(
            master = self,
            width = 500,
            text = "Laser Mask Parameters",
            corner_radius = 5,
            fg_color = "grey23"
        )
        self.lbl_frm.grid(row=0, column=0, padx=5, pady=5, sticky="nesw", columnspan=5)
        # create laser image control group
        self.lbl_cr1 = customtkinter.CTkLabel(master=self, text="Crop Mask to:")
        self.lbl_cr1.grid(row=1, column=0, padx=(10, 0), pady=5, sticky="nesw")
        self.inp_crx = customtkinter.CTkEntry(
            master = self,
            textvariable = tkinter.StringVar(
                master = self,
                value = PARAMS_CRP[1]
            )
        )
        self.inp_crx.grid(row=1, column=1, padx=(5, 0), pady=5, sticky="nesw")
        self.lbl_cr2 = customtkinter.CTkLabel(master=self, text="(px)   by  ")
        self.lbl_cr2.grid(row=1, column=2, padx=0, pady=5, sticky="nesw")
        self.inp_cry = customtkinter.CTkEntry(
            master = self,
            textvariable = tkinter.StringVar(
                master = self,
                value = PARAMS_CRP[1]
            )
        )
        self.inp_cry.grid(row=1, column=3, padx=0, pady=5, sticky="nesw")
        self.lbl_cr3 = customtkinter.CTkLabel(master=self, text="(px)")
        self.lbl_cr3.grid(row=1, column=4, padx=(0, 5), pady=5, sticky="nesw")
        # create slider and other controls
        self.frm_sld = Sld(master=self)
        self.frm_sld.grid(row=2, column=0, padx=5, pady=5, sticky="nesw", columnspan=5)
        self.frm_rdm = Rdm(master=self)
        self.frm_rdm.grid(row=3, column=0, padx=5, pady=(0,5), sticky="nesw", columnspan=5)


class Sld(customtkinter.CTkFrame):
    """
    Class: ctk frame for the crop/resize control of laser mask.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        # -------------------------------------- GUI setting --------------------------------------
        self.lbl_iu0 = customtkinter.CTkLabel(master=self, text="px: ")
        self.lbl_iu0.grid(row=0, column=0, padx=(15,0), pady=5, sticky="nesw")
        self.lbl_iu1 = customtkinter.CTkLabel(master=self, text="IU: ")
        self.lbl_iu1.grid(row=2, column=0, padx=(15,0), pady=5, sticky="nesw")
        for i in range(0, 11):
            sc1 = customtkinter.CTkLabel(
                master = self,
                width = 30,
                text = str(PARAMS_CRP[0] - PARAMS_CRP[2]*i)
            )
            sc1.grid(row=0, column=11-i, padx=5, pady=5, sticky="nesw")
            sc2 = customtkinter.CTkLabel(
                master = self,
                width = 30,
                text = str(int((PARAMS_CRP[0] - PARAMS_CRP[2]*i)/192*25))
            )
            sc2.grid(row=2, column=11-i, padx=5, pady=5, sticky="nesw")
            if i < 3:
                sc1.configure(text_color="#B62B24")
                sc2.configure(text_color="#B62B24")
        self.pgb_inp = customtkinter.CTkProgressBar(master=self)
        self.pgb_inp.set(0.7)
        self.pgb_inp.grid(row=1, column=1, padx=16, pady=5, sticky="nesw", columnspan=12)
        self.sld_inp = customtkinter.CTkSlider(
            master = self,
            from_ = 0,
            to = 1,
            number_of_steps = 10,
            command = self.sld_upd
        )
        self.sld_inp.set(0.7)
        self.sld_inp.grid(row=3, column=1, padx=12, pady=5, sticky="nesw", columnspan=12)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on call ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def sld_upd(self, _self):
        """
        Function: update slider values to master class's label.
        """
        # update image crop configurations
        self.master.inp_crx.configure(textvariable = tkinter.StringVar(
                master = self,
                value = round(PARAMS_CRP[3] + PARAMS_CRP[2]*self.sld_inp.get()*10)
        ))
        self.master.inp_cry.configure(textvariable = tkinter.StringVar(
                master = self,
                value = round(PARAMS_CRP[3] + PARAMS_CRP[2]*self.sld_inp.get()*10)
        ))
        # update slider bar configurations
        self.pgb_inp.set(self.sld_inp.get())
        # update mask subdivision settings
        self.master.frm_rdm.lbl_num.configure(text=pow(round(self.sld_inp.get()*10 + 2),2))


class Rdm(customtkinter.CTkFrame):
    """
    Class: ctk frame for controling further mask modifications.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        # -------------------------------------- GUI setting --------------------------------------
        self.lbl_rvs = customtkinter.CTkLabel(master=self, text="Coloring:")
        self.lbl_rvs.grid(row=0, column=0, padx=(15,5), pady=5, sticky="nesw")
        self.btn_rvs = customtkinter.CTkSegmentedButton(master=self, values=["Normal","Reversed"])
        self.btn_rvs.set("Normal")
        self.btn_rvs.grid(row=0, column=1, padx=(5,15), pady=5, sticky="nesw")
        self.lbl_cfr = customtkinter.CTkLabel(master=self, text="Expected Division:")
        self.lbl_cfr.grid(row=0, column=2, padx=(15,0), pady=5, sticky="nesw")
        self.lbl_num = customtkinter.CTkLabel(master=self, width=25, text="81")
        self.lbl_num.grid(row=0, column=3, padx=(5,5), pady=5, sticky="nesw")
        self.lbl_pct = customtkinter.CTkLabel(master=self, text="Images (25x25 IU)")
        self.lbl_pct.grid(row=0, column=4, padx=(0,15), pady=5, sticky="nesw")


class Cp2(customtkinter.CTkFrame):
    """
    Class: ctk frame for cellpose parameter control and inputs.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        # -------------------------------------- GUI setting --------------------------------------
        # create label as the frame header
        self.lbl_frm = customtkinter.CTkLabel(
            master = self,
            text = "Cellpose 2 Parameters",
            corner_radius = 5,
            fg_color = "grey23"
        )
        self.lbl_frm.grid(row=0, column=0, padx=(5, 5), pady=5, sticky="nesw", columnspan=6)
        # set dropdown for cell model type
        self.lbl_mdl = customtkinter.CTkLabel(
            master = self,
            anchor = "e",
            text = "Cellpose Model Type:"
        )
        self.lbl_mdl.grid(row=1, column=0, padx=(10, 5), pady=5, sticky="nesw")
        self.inp_mdl = customtkinter.CTkComboBox(master=self, values=PARAMS_MOD)
        self.inp_mdl.grid(row=1, column=1, padx=(5, 5), pady=5, sticky="nesw")
        # set box for cell pixel diameters
        self.lbl_dim = customtkinter.CTkLabel(
            master = self,
            anchor = "e",
            text = "Cell Diameter (px):"
        )
        self.lbl_dim.grid(row=1, column=2, padx=(10, 5), pady=5, sticky="nesw")
        self.inp_dim = customtkinter.CTkEntry(
            master = self,
            textvariable = tkinter.StringVar(master=self, value=PARAMS_CPD)
        )
        self.inp_dim.grid(row=1, column=3, padx=(5, 5), pady=5, sticky="nesw")
        # set segmentation channels (arbg)
        self.lbl_sgm = customtkinter.CTkLabel(
            master = self,
            anchor = "e",
            text = "Segmentation Channel:"
        )
        self.lbl_sgm.grid(row=1, column=4, padx=(10, 5), pady=5, sticky="nesw")
        self.inp_sgm = customtkinter.CTkOptionMenu(master=self, values=PARAMS_CNL)
        self.inp_sgm.grid(row=1, column=5, padx=(5, 10), pady=5, sticky="nesw")


class Top(customtkinter.CTkToplevel):
    """
    Class: ctk top level window for checking commence progress.
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on enable ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        # ---------------------------------- application setting ----------------------------------
        self.title("Export Progress")
        self.geometry("400x100")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        # -------------------------------------- GUI setting --------------------------------------
        self.lbl_txt = customtkinter.CTkLabel(master=self, text="Constructing Laser Mask")
        self.lbl_txt.grid(row=0, column=0, padx=10, pady=5, sticky="nesw")
        self.pgb_prg = customtkinter.CTkProgressBar(master=self)
        self.pgb_prg.set(0)
        self.pgb_prg.grid(row=1, column=0, padx=10, pady=5, sticky="nesw")


# ===================================== independent functions =====================================

def create_cpmask_single(
        original,               # file name with path to the original image
        exported,               # file name with path to the exported image
        cropsize = None,        # mask crop size for output [width, height]
        reversal = False,       # reverse output image color if set to true
        cp2model = "cyto3",     # cellpose model type for cell segmentation
        diameter = 30,          # average pixel diameter for a typical cell
        channels = None,        # segmentation channel [cytoplasm, nucleus]
):
    """
    ### Construct and save cp2 image masks for a list of image files with paths.

    `original` : file name and path to the original images.
    `exported` : file name and path to the exported images.
    -----------------------------------------------------------------------------------------------
    #### Optional:
    `cropsize` : size of the output images [width, height] = *(same as input image)*.
    `reversal` : reverse output image color if set to true = `False`.
    `cp2model` : cellpose model type for cell segmentation = `"cyto3"`.
    `diameter` : average pixel diameter for a typical cell = `30`.
    `channels` : segmentation channel [cytoplasm, nucleus] = `[0,0]`.
    """
    # ------------------------------------ variable processing ------------------------------------
    io.logger_setup()
    # set cellpose model and cell mask segmentation channels
    cp2 = models.Cellpose(gpu=True, model_type=cp2model)
    if channels is None:
        channels = [0,0]
    # initialize cp2 inputs, save mask to original file path
    img = io.imread(original)
    masks, flows, _styles, _diams = cp2.eval(img, diameter=float(diameter), channels=channels)
    io.save_masks(img, masks, flows, original, png=True, tif=False, save_txt=False)
    # predict paths for saved mask, delete file after opened
    msk = Image.open(os.path.splitext(original)[0] + '_cp_masks.png')
    # remove color grading, convert png mask to binary image
    for i in range(msk.size[0]):
        for j in range(msk.size[1]):
            if msk.load()[i,j] > 0:
                msk.load()[i,j] = 255
    # crop the output mask image based on cropsize parameter
    if cropsize is None:
        cropsize = msk.size
    tmp = Image.new('L', cropsize, 0)
    tmp.paste(msk, [round((cropsize[0]-msk.size[0])/2), round((cropsize[1]-msk.size[1])/2)])
    # invert mask color if image color reversal is activated
    if reversal is False:
        tmp = ImageChops.invert(tmp)
    # copy the cropped mask to a new blank image and save it
    msk = Image.new('L', cropsize, 0)
    msk.paste(tmp, [round((cropsize[0]-tmp.size[0])/2), round((cropsize[1]-tmp.size[1])/2)])
    rtn = Image.new('L', PARAMS_FOV, 255)
    rtn.paste(msk, [round((PARAMS_FOV[0]-msk.size[0])/2), round((PARAMS_FOV[1]-msk.size[1])/2)])
    rtn = rtn.resize(PARAMS_MSK)
    rtn.save(exported)
    os.remove(os.path.splitext(original)[0] + '_cp_masks.png')


# ========================================= main function =========================================

def mercury_02():
    """
    Main application loop of mercury 02, save laser mask image and return 0.
    """
    # set customtkinter appearance mode and color theme
    customtkinter.set_appearance_mode("dark")
    customtkinter.set_default_color_theme("blue")
    # enter main loop and return 0 when export finishes
    app = App()
    app.resizable(False, False)
    app.mainloop()
    return 0
