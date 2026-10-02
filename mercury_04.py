"""
Mercury 04: image stitching previews, project version 1.26 (with python 3.9).
"""

import os
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
import customtkinter
import matplotlib.pyplot as plt
from PIL import Image
from matplotlib.colors import ListedColormap

from mercury_00 import convert_to_rgba
from mercury_01 import ctk_entry_warning
from mercury_02 import read_xycoordinates, plot_rectangles, FileInput

# from params import PARAMS_DTP
from params import PARAMS_EXP
from params import PARAMS_MCI
from params import PARAMS_MSK
from params import PARAMS_LSR
from params import PARAMS_MAP
from params import PARAMS_PLN
# from params import PARAMS_CRD
from params import PARAMS_GLB
# from params import PARAMS_SCT
from params import PARAMS_BIT
# from params import PARAMS_TMP
# from params import PARAMS_VER

from params import CONSTS_MULT_FOVS
from params import CONSTS_MASK_SIZE

# ctk window title
WINDOW_TXT = "Mercury IV - Image Stitching Preview"
# stitched image types (ctk segmented button values)
PARAMS_TYP = ["Multichannel Images", "Laser Masks", "Laser Images"]
# stitch scale: stitched image px per global mask px (1 = same px frame as the bit scheme)
PARAMS_SCL = 1
# stitched multichannel image and mask file names (saved in experiment folder)
PARAMS_GMI = "image_multi_global.png"
PARAMS_GMK = "image_mask_global (recomputed).png"
# stitched laser image file name of each round (saved in cleave map folder)
PARAMS_GLS = "Round {} (laser).png"
# alpha value of each laser image (half-transparent, so overlaps and illuminations are visible)
PARAMS_ALP = 128
# barcode overlay colors: not cleaved / cleaved in the selected round
PARAMS_CL0 = "red"
PARAMS_CL1 = "green"
# stitched images can exceed pillow's decompression bomb limit, disable the check
Image.MAX_IMAGE_PIXELS = None


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
        self.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="group")
        self.grid_rowconfigure(0, weight=1)
        self.thread:threading.Thread = None
        self.result:tuple = None
        self.txt_prg = ""
        self.flt_prg = 0.0
        # -------------------------------------- GUI setting --------------------------------------
        # prompt user for experiment folder path
        self.frm_ctl = FileInput(master=self, str_textvar=PARAMS_EXP)
        self.frm_ctl.grid(row=0, column=0, padx=10, pady=(10,5), sticky="nesw", columnspan=4)
        # select image type, and round index (for laser images and highlighting barcodes)
        self.seg_typ = customtkinter.CTkSegmentedButton(master=self, values=PARAMS_TYP)
        self.seg_typ.set(PARAMS_TYP[0])
        self.seg_typ.grid(row=1, column=0, padx=(10,5), pady=5, sticky="nesw", columnspan=3)
        self.ent_rnd = customtkinter.CTkEntry(
            master = self,
            placeholder_text = "(Round Index)"
        )
        self.ent_rnd.grid(row=1, column=3, padx=(0,10), pady=5, sticky="nesw", columnspan=1)
        # preview and commence (stitch & save) buttons
        self.btn_prv = customtkinter.CTkButton(
            master = self,
            text = "Preview Stitching",
            command = lambda: self.app_cmc(save=False),
            fg_color = "transparent",
            border_width = 1,
            hover_color = "gray23"
        )
        self.btn_prv.grid(row=2, column=0, padx=(10,5), pady=5, sticky="nesw", columnspan=2)
        self.btn_cmc = customtkinter.CTkButton(
            master = self,
            text = "Stitch & Save",
            command = lambda: self.app_cmc(save=True)
        )
        self.btn_cmc.grid(row=2, column=2, padx=(0,10), pady=5, sticky="nesw", columnspan=2)
        # progress bar (shown once stitching starts) and label to display information
        self.pgb_prg = customtkinter.CTkProgressBar(master=self)
        self.pgb_prg.set(0)
        self.lbl_inf = customtkinter.CTkLabel(
            master=self, text="", font=customtkinter.CTkFont(size=10)
        )
        self.lbl_inf.grid(row=4, column=0, padx=10, pady=(0,5), sticky="nesw", columnspan=4)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ on call ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def app_cmc(self, save = False):
        """
        Function: stitch selected images in a separate thread, then preview (or save) results.
        """
        # read experiment folder, check if it's a valid folder path
        exp_folder, successful = self.frm_ctl.get_entry(check_for_folder=True)
        if not successful:
            self.lbl_inf.configure(text=exp_folder)
            return
        # read round index (empty or -1 = all rounds, no highlighted barcodes)
        try:
            num_round = int(self.ent_rnd.get()) if self.ent_rnd.get().strip() != "" else -1
            if num_round < -1:
                raise ValueError
        except ValueError:
            ctk_entry_warning(self.ent_rnd)
            self.lbl_inf.configure(text="Warning: round index must be -1 (all rounds) or >= 0")
            return
        # disable buttons, show progress bar, run stitching on new thread, check back until done
        self.btn_prv.configure(state="disabled")
        self.btn_cmc.configure(state="disabled")
        self.pgb_prg.grid(row=3, column=0, padx=10, pady=(10,0), sticky="nesw", columnspan=4)
        self.result = None
        self.set_progress("Initializing ...", 0)
        self.thread = threading.Thread(
            target = self.thread_stitch,
            args = (exp_folder, self.seg_typ.get(), num_round, save),
            daemon = True
        )
        self.thread.start()
        self.after(100, self.wait_thread)
    # ---------------------------------------------------------------------------------------------
    def thread_stitch(self, exp_folder, image_type, num_round, save):
        """
        Function: stitch (and save) images in a separate thread, keep results for previewing.
        """
        try:
            frame = global_frame(exp_folder)
            background = None
            overlay = None
            text = ""
            title = f"{os.path.basename(exp_folder)} - {image_type}"
            if image_type == PARAMS_TYP[2] and num_round < 0 and not save:
                # preview all rounds: global mask, outline missing laser images and tally them
                image = stitch_tiles(exp_folder, frame, True, self.set_progress)
                overlay, text = tally_laser_images(exp_folder, list_laser_images(exp_folder))
                title += " (all rounds)"
            elif image_type == PARAMS_TYP[2]:
                # stitch laser images of the selected round, or all rounds (-1)
                laser_images = list_laser_images(exp_folder)
                rounds = list_rounds(exp_folder) if num_round < 0 else [num_round]
                for i in rounds:
                    image = stitch_laser(
                        exp_folder, frame, i, laser_images.get(i, {}), self.set_progress
                    )
                    if save:
                        self.set_progress(f"Saving laser images of round {i} ...", 1)
                        image.save(os.path.join(exp_folder, PARAMS_MAP, PARAMS_GLS.format(i)))
                message = f"Saved {len(rounds)} stitched laser image(s) in \"{PARAMS_MAP}\""
                # show cleave map of the round as background
                file_path = os.path.join(exp_folder, PARAMS_MAP, f"Round {num_round}.png")
                if not save and os.path.isfile(file_path):
                    background = Image.open(file_path).convert('L')
            else:
                # stitch multichannel images or laser masks
                is_mask = image_type == PARAMS_TYP[1]
                image = stitch_tiles(exp_folder, frame, is_mask, self.set_progress)
                if save:
                    self.set_progress(f"Saving stitched {image_type.lower()} ...", 1)
                    image.save(os.path.join(exp_folder, PARAMS_GMK if is_mask else PARAMS_GMI))
                message = f"Saved \"{PARAMS_GMK if is_mask else PARAMS_GMI}\" in experiment folder"
            # keep results and barcode overlays for previewing
            if not save:
                message = "Stitching preview is ready"
                if overlay is None:
                    overlay = load_barcodes(exp_folder, frame, num_round, self.set_progress)
                if num_round >= 0:
                    title += f" (round {num_round})"
                self.result = (image, background, overlay, text, title)
            self.set_progress(message, 1)
        except (ValueError, IndexError, KeyError, TypeError, OSError, MemoryError) as e:
            traceback.print_exc()
            self.set_progress(f"Warning: cannot stitch {image_type.lower()} - {e}", 0)
    # ---------------------------------------------------------------------------------------------
    def set_progress(self, text, ratio):
        """
        Function: store progress text and ratio (shown by the main thread).
        """
        self.txt_prg = text
        self.flt_prg = ratio
    # ---------------------------------------------------------------------------------------------
    def wait_thread(self):
        """
        Function: show progress until the stitching thread is finished, then show the preview.
        """
        if self.thread.is_alive():
            self.after(100, self.wait_thread)
        else:
            self.btn_prv.configure(state="normal")
            self.btn_cmc.configure(state="normal")
            # pyplot has to run on the main thread
            if self.result is not None:
                preview_stitching(*self.result)
                self.result = None
        self.lbl_inf.configure(text=self.txt_prg)
        self.pgb_prg.set(self.flt_prg)
    # ---------------------------------------------------------------------------------------------
    def on_closing(self):
        """
        Function: enforce quit manually before closing (close previews as well).
        """
        plt.close('all')
        self.quit()


# ===================================== independent functions =====================================

def list_files(folder, file_endswith):
    """
    Function: return file names in a folder that end with a specific trail, sorted by name.
    """
    if not os.path.isdir(folder):
        return []
    return sorted([f for f in os.listdir(folder) if f.endswith(file_endswith)])


def list_laser_images(exp_folder):
    """
    Function: return laser image file names as {round index: {area index: file name}}.
    laser image file names start with "{1000 + round index}_{1000 + area index}".
    """
    rtn = {}
    for file in list_files(os.path.join(exp_folder, PARAMS_LSR), ".tif"):
        try:
            num_round = int(file[0:4]) - 1000
            num_area = int(file[5:9]) - 1000
        except ValueError:
            continue
        rtn.setdefault(num_round, {})[num_area] = file
    return rtn


def list_rounds(exp_folder):
    """
    Function: return all round indexes, found from cleave map coordinates ("Round {i}.csv").
    """
    files = list_files(os.path.join(exp_folder, PARAMS_MAP), ".csv")
    rtn = sorted([int(f[6:-4]) for f in files if f.startswith("Round ") and f[6:-4].isdigit()])
    if len(rtn) == 0:
        raise FileNotFoundError(f"no cleave map coordinates found in \"{PARAMS_MAP}\"")
    return rtn


def tally_laser_images(exp_folder, laser_images):
    """
    Function: compare expected laser images (scan areas of all rounds) with saved laser images.
    returns ("missing", px bounds of missing laser images, all True) and a tally text.
    """
    bounds = []
    num_saved, num_expected = 0, 0
    txt = "Laser images (saved / expected):"
    for i in list_rounds(exp_folder):
        # scan areas of the round (area index as dataframe index), marked if an image is saved
        df = pd.read_csv(os.path.join(exp_folder, PARAMS_MAP, f"Round {i}.csv"), index_col=0)
        saved = df.index.isin(list(laser_images.get(i, {})))
        bounds.append(df.loc[~saved, ['w','n','e','s']].values * PARAMS_SCL)
        num_saved += int(saved.sum())
        num_expected += len(df)
        txt += f"\nRound {i}: {int(saved.sum())} / {len(df)}"
    txt += f"\nTotal: {num_saved} / {num_expected}\n\nMissing laser images: {PARAMS_CL1}"
    bounds = np.concatenate(bounds)
    return (("missing", bounds, np.ones(len(bounds), dtype=bool)), txt)


def global_frame(exp_folder):
    """
    Function: return the global image frame, same as the global mask stitched by mercury 02.

    Returns *(image size, tile size, multichannel coordinates, position function)*, where the
    position function returns the top-left corner (px) of a tile centered at stage coordinates
    (um). The tissue range (padded by half a FOV) is centered in the global mask if it exists.
    """
    # acquire multichannel coordinates
    coords = read_xycoordinates(os.path.join(exp_folder, PARAMS_PLN))
    # mask px size from the first mask image (mercury 02 pastes masks at their native size)
    mask_px = CONSTS_MASK_SIZE
    masks = list_files(os.path.join(exp_folder, PARAMS_MSK), ".png")
    if len(masks) != 0:
        with Image.open(os.path.join(exp_folder, PARAMS_MSK, masks[0])) as img:
            mask_px = img.size[0]
    mask_px_per_um = mask_px / CONSTS_MULT_FOVS
    # find min/max x and y values from multichannel image coordinates (um)
    min_x_um = min(x for x, y in coords)
    max_x_um = max(x for x, y in coords)
    min_y_um = min(y for x, y in coords)
    max_y_um = max(y for x, y in coords)
    # tissue range, padded by half a FOV on each side (one full FOV total)
    range_x_px = round((max_x_um - min_x_um + CONSTS_MULT_FOVS) * mask_px_per_um)
    range_y_px = round((max_y_um - min_y_um + CONSTS_MULT_FOVS) * mask_px_per_um)
    # global mask size, fit to the tissue range if there's no global mask
    width, height = range_x_px, range_y_px
    if os.path.isfile(os.path.join(exp_folder, PARAMS_GLB)):
        with Image.open(os.path.join(exp_folder, PARAMS_GLB)) as img:
            width, height = img.size
    # top-left corner of the tissue range inside the global mask
    start_x_px = round((width - range_x_px) / 2)
    start_y_px = round((height - range_y_px) / 2)
    def position(x_um, y_um):
        # paste position: start + (um offset from corner) * scale (same as mercury 02)
        x_px = round(start_x_px + (x_um - min_x_um) * mask_px_per_um)
        y_px = round(start_y_px + (max_y_um - y_um) * mask_px_per_um)
        return (round(x_px * PARAMS_SCL), round(y_px * PARAMS_SCL))
    size = (round(width * PARAMS_SCL), round(height * PARAMS_SCL))
    return (size, round(mask_px * PARAMS_SCL), coords, position)


def load_tile(file_path, tile, is_mask = False):
    """
    Function: read an image, resize it to tile size, and rotate it by 180 deg to adjust for the
    inversion effect from the microscope (masks are converted to grayscale with their palette).
    """
    img = Image.open(file_path)
    if is_mask:
        img = img.convert('L').resize([tile, tile], Image.Resampling.NEAREST)
    else:
        img = img.resize([tile, tile], Image.Resampling.BOX)
    return img.transpose(Image.Transpose.ROTATE_180)


def stitch_tiles(exp_folder, frame, is_mask, progress):
    """
    Function: stitch multichannel images (16-bit) or laser masks (8-bit) into a global image.
    """
    size, tile, coords, position = frame
    # acquire image paths
    folder = os.path.join(exp_folder, PARAMS_MSK if is_mask else PARAMS_MCI)
    images = list_files(folder, ".png" if is_mask else ".tif")
    # check list lengths
    if len(images) != len(coords):
        raise IndexError(f"found {len(images)} images, {len(coords)} coordinate pairs")
    # masks have white background, 16-bit multichannel images have black background
    img = Image.new('L', size, 255) if is_mask else Image.new('I;16', size)
    # read images in parallel, paste them in order
    name = "laser masks" if is_mask else "multichannel images"
    with ThreadPoolExecutor() as pool:
        tiles = pool.map(lambda file: load_tile(os.path.join(folder, file), tile, is_mask), images)
        for i, tmp in enumerate(tiles):
            img.paste(tmp, position(*coords[i]))
            progress(f"Stitching {name} ... ({i+1}/{len(images)})", i/len(images))
    return img


def stitch_laser(exp_folder, frame, num_round, laser_images, progress):
    """
    Function: stitch laser images of a round into a global RGBA image, each laser image is
    half-transparent so that overlaps and laser illuminations are both visible.
    areas without laser images are left blank (transparent).
    """
    size, tile, _coords, position = frame
    # acquire laser scan coordinates of the round (area index as dataframe index)
    df = pd.read_csv(os.path.join(exp_folder, PARAMS_MAP, f"Round {num_round}.csv"), index_col=0)
    areas = [area for area in sorted(laser_images) if area in df.index]
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    # read images in parallel, paste them in order
    with ThreadPoolExecutor() as pool:
        tiles = pool.map(
            lambda area: load_tile(os.path.join(exp_folder, PARAMS_LSR, laser_images[area]), tile),
            areas
        )
        for i, (area, tmp) in enumerate(zip(areas, tiles)):
            # laser images are taken at offset-compensated coordinates (if recorded by mercury 03)
            x_um, y_um = df.loc[area, 'x'], df.loc[area, 'y']
            if 'x_adj' in df.columns and pd.notna(df.loc[area, 'x_adj']):
                x_um, y_um = df.loc[area, 'x_adj'], df.loc[area, 'y_adj']
            # convert to half-transparent 8-bit image, paste (crop parts outside of the image)
            tmp = convert_to_rgba(tmp, alpha=PARAMS_ALP)
            x_px, y_px = position(x_um, y_um)
            img.alpha_composite(
                tmp, dest=(max(x_px, 0), max(y_px, 0)), source=(max(-x_px, 0), max(-y_px, 0))
            )
            progress(
                f"Stitching laser images of round {num_round} ... ({i+1}/{len(areas)})",
                i/len(areas)
            )
    return img


def load_barcodes(exp_folder, frame, num_round, progress):
    """
    Function: load barcode overlays, decided by the bit scheme (return None if it doesn't exist).
    returns ("grid", submask px bounds, cleaved) or ("cell", cell outline image, cleaved), where
    cleaved marks barcodes cleaved in the selected round.
    """
    file_path = os.path.join(exp_folder, PARAMS_BIT)
    if not os.path.isfile(file_path):
        return None
    df = pd.read_csv(file_path, index_col=0)
    # bit string "[1, 0, ...]": check if each barcode is cleaved in the selected round
    cleaved = np.zeros(len(df), dtype=bool)
    if num_round >= 0:
        cleaved = (df['bit'].str.strip('[]').str.split(', ').str[num_round] == '1').values
    # grid-based submasks: (w, n, e, s) px bounds on the global mask
    if df['w'].notna().any():
        return ("grid", df[['w','n','e','s']].values * PARAMS_SCL, cleaved)
    # cell-based: outline cells in cell arrays, cells are counted the same way as mercury 02
    size, tile, coords, position = frame
    folder = os.path.join(exp_folder, PARAMS_MSK)
    arrays = list_files(folder, ".npz")
    if len(arrays) != len(coords):
        raise IndexError(f"found {len(arrays)} cell arrays, {len(coords)} coordinate pairs")
    img = Image.new('L', size, 0)
    count = 0
    for i, file in enumerate(arrays):
        masks = np.load(os.path.join(folder, file))["masks"]
        tmp = Image.fromarray(masks.astype(np.int32))
        tmp = tmp.resize([tile, tile], Image.Resampling.NEAREST)
        cells = np.asarray(tmp.transpose(Image.Transpose.ROTATE_180))
        # outline: cell pixels next to other cells/background (1 = not cleaved, 2 = cleaved)
        inner = np.zeros(cells.shape, dtype=bool)
        inner[1:-1, 1:-1] = (
            (cells[1:-1, 1:-1] == cells[:-2, 1:-1]) & (cells[1:-1, 1:-1] == cells[2:, 1:-1]) &
            (cells[1:-1, 1:-1] == cells[1:-1, :-2]) & (cells[1:-1, 1:-1] == cells[1:-1, 2:])
        )
        edge = (cells > 0) & ~inner
        outline = np.zeros(cells.shape, dtype=np.uint8)
        outline[edge] = 1 + cleaved[count + cells[edge] - 1]
        img.paste(Image.fromarray(outline), position(*coords[i]))
        count += int(masks.max())
        progress(f"Outlining cells ... ({i+1}/{len(arrays)})", i/len(arrays))
    return ("cell", np.asarray(img), cleaved)


def preview_stitching(image, background, overlay, text, title):
    """
    Function: construct pyplot preview for a stitched image, with overlays and text description.
    """
    extent = (0, image.size[0], image.size[1], 0)
    # wider figure if there's a textbox on the side
    plt.figure(figsize=(13 if text != "" else 10, 10)).canvas.manager.set_window_title(title)
    # show cleave map as background (for laser images), then stitched image (auto-scaled)
    if background is not None:
        plt.imshow(background, cmap='gray', vmin=0, vmax=255, extent=extent)
    plt.imshow(image, cmap='gray', extent=extent)
    # show cells as outlines, grid submasks (or missing laser images) as rectangles
    if overlay is not None and overlay[0] == "cell":
        plt.imshow(
            np.ma.masked_equal(overlay[1], 0),
            cmap=ListedColormap([PARAMS_CL0, PARAMS_CL1]),
            vmin=1,
            vmax=2,
            extent=extent,
            interpolation='nearest'
        )
    elif overlay is not None:
        _kind, bounds, cleaved = overlay
        centers = np.column_stack([bounds[:, [0, 2]].mean(axis=1), bounds[:, [1, 3]].mean(axis=1)])
        for select, color in ((~cleaved, PARAMS_CL0), (cleaved, PARAMS_CL1)):
            if select.any():
                plot_rectangles(
                    centers[select],
                    width=bounds[0, 2] - bounds[0, 0],
                    height=bounds[0, 3] - bounds[0, 1],
                    color=color,
                    alpha=1,
                    linewidth=0.5
                )
    # create textbox to display relevant information
    if text != "":
        plt.text(
            x = 1.05,
            y = 1,
            s = text,
            transform = plt.gca().transAxes,
            fontsize = 10,
            verticalalignment='top',
            bbox = dict(facecolor='none', alpha=0.15)
        )
    # show plot preview window
    plt.title(title)
    plt.gca().set_aspect('equal')
    plt.tight_layout()
    plt.show(block=False)


# ========================================= main function =========================================

def mercury_04():
    """
    Main application loop of mercury 04, display stitching previews and save stitched images.
    """
    # set customtkinter appearance mode and color theme
    customtkinter.set_appearance_mode("dark")
    customtkinter.set_default_color_theme("blue")
    # enter main loop
    app = App()
    app.resizable(False, False)
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.attributes("-topmost", True)
    app.after_idle(app.attributes, "-topmost", False)
    app.after(10, app.focus)
    app.mainloop()

if __name__ == "__main__":
    print(mercury_04())
