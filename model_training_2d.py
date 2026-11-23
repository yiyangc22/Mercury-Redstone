# pylint: disable = line-too-long, too-many-lines
"""
Model Training 2D
Outline cells by hand on a single-channel TIFF image, check the outlines in ImageJ, and save everything Cellpose 3 or
Cellpose-SAM (Cellpose 4) needs to train on it. The window is plain tkinter (Python's own), for Windows, Linux and macOS.

Drawing a cell: left-click its corners one by one, then double-click to finish (Enter, or a click on the first corner,
also finishes). Straight sides cut inside a curved edge, so use enough corners: about 12 follow a round cell closely.
    right-click             while drawing: take back the last corner (as do Backspace and Ctrl+Z)
                            otherwise: delete the cell under the mouse
    Escape                  drop the whole outline being drawn
    mouse wheel             zoom in / out around the mouse
    Shift + left-drag (or middle-drag)   move the view;   F (or Fit view) shows the whole image again
    Ctrl+Z / Ctrl+Y         undo / redo (Ctrl+Shift+Z also redoes), back to when the image was opened
    Ctrl+O / Ctrl+S         open / save
On a Mac, Cmd can be used instead of Ctrl, and Ctrl + click is a right-click. (The Mac parts have not been tried on a
Mac yet: see on_scroll for the one most likely to need adjusting.)
An outline that cannot be added (it crosses itself, or overlaps a cell in a way that cannot be cut, see below) stays on
the screen with the reason in the status line, to be corrected (right-click takes back corners) or dropped (Escape).

Overlaps: where a new outline crosses a cell's outline at two points, the overlap is cut along the straight line between
those two points. Each cell keeps the part on its own side, so both outlines change. (Where one of the two outlines is
already straight across the overlap, that side is the line, and that cell keeps all of the overlap.) One undo takes
back the new cell and the cut together. A new outline is not added if it lies inside a cell or goes around one, touches
a cell's outline exactly at a corner, or makes an overlap that one straight line cannot cut (for example a cross).

Saved next to the image (the image itself is never changed), for an image <name>.tif:
    <name>_masks.tif     the cells in Cellpose's label format: 0 = background, 1, 2, 3, ... = cell 1, 2, 3, ... (uint16)
    <name>_RoiSet.zip    the outlines as ImageJ polygon ROIs named cell_001, cell_002, ... (cell_001 = 1 in the masks)
Opening the image again brings its outlines back from <name>_RoiSet.zip.
The masks are made from the outlines: a pixel belongs to a cell if the pixel's centre is inside its outline.

Checking the outlines in ImageJ (or Fiji):
    1. open the image
    2. drag <name>_RoiSet.zip onto the ImageJ window (or, in the ROI Manager: More > Open...)
    3. in the ROI Manager, tick Show All (and Labels): every outline is drawn on the image; click a name to select it
Correcting an outline in ImageJ: select it, change it, press Update, then More > Save... over <name>_RoiSet.zip. Then
open the image here again and press Save, so that <name>_masks.tif is made again from the corrected outlines.
Polygon, freehand, traced (wand), rectangle and oval ROIs can be read back; lines, points, composite and spline-fitted
ROIs cannot (the program lists them, and can open the image without them).
ImageJ puts the centre of the top-left pixel at (0.5, 0.5) and this program at (0, 0), so 0.5 is added to every
coordinate when saving and taken away when reading.

Training on a folder of outlined images (in a terminal, in the environment that has Cellpose):
    Cellpose 3:
        python -m cellpose --train --dir "<folder>" --pretrained_model cyto3 --chan 0 --chan2 0 --use_gpu
    Cellpose-SAM (cellpose 4):
        python -m cellpose --train --dir "<folder>" --pretrained_model cpsam --use_gpu
    - Every image in the folder needs its <name>_masks.tif: if one is missing, Cellpose stops with "labels not provided
      for all images". So keep the training images in a folder of their own, and outline every one of them.
    - Cellpose leaves out images with fewer than 5 cells; add --min_train_masks 1 to keep them.
    - The trained model is saved in <folder>/models (a Cellpose-SAM model is about 1.2 GB).
    - Cellpose leaves <name>_flows.tif files in the folder (worked out from the masks); saving here deletes the image's
      old one, so edited outlines are never trained on stale flows.
    - Cellpose ignores the _RoiSet.zip files.

Needs numpy, tifffile, roifile and matplotlib (tkinter comes with Python, and roifile comes with Cellpose).
Run: python model_training_2d.py  (or: python model_training_2d.py <image.tif> to open an image straight away)
"""

# pylint: disable = broad-exception-caught
# pylint: disable = unused-argument
# pylint: disable = too-many-instance-attributes
# pylint: disable = too-many-public-methods
# pylint: disable = too-many-statements
# pylint: disable = too-many-return-statements
# pylint: disable = too-many-arguments
# pylint: disable = too-many-positional-arguments
# pylint: disable = too-many-locals
# pylint: disable = too-many-branches
# pylint: disable = chained-comparison
# pylint: disable = consider-using-in

import os
import sys
import math
import time
import tkinter
from tkinter import filedialog, messagebox
import numpy as np
import tifffile
import roifile
from matplotlib.figure import Figure
from matplotlib.path import Path
from matplotlib.collections import PolyCollection
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# the folder this program is in (where the first Open image starts); every path is built with os.path.join, so the
# program runs on Windows, Linux and macOS. The masks and outlines are saved next to each image.
PROGRAM_FOLDER = os.path.dirname(os.path.abspath(__file__))

MIN_CELL_PIXELS = 10      # an outline that would get fewer pixels than this is not added (a slip of the mouse)
CLOSE_DISTANCE = 10       # screen pixels: a click this close to the first corner finishes the outline
MIN_TRAIN_MASKS = 5       # Cellpose's default: images with fewer cells are left out of training
ZOOM_STEP = 1.25          # each step of the mouse wheel shows 1.25 times less (in) or more (out) of the image
MIN_VIEW_PIXELS = 10      # the view never zooms in closer than this many image pixels across
IMAGEJ_OFFSET = 0.5       # ImageJ coordinate = this program's coordinate + 0.5
TINY = 1e-9               # crossings closer than this (as a fraction of a side) to a side's end count as touching
MAX_CUT_STRAY = 1.0       # pixels: how far the straight cut through a thin, bent overlap may run outside the two outlines
MAC_SCROLL_INTERVAL = 0.1 # on a Mac, at most one zoom step per this many seconds (a trackpad sends a stream of scrolls)

CELL_EDGE_COLOR = "#00E5FF"     # outline of a finished cell (cyan)
CELL_FILL_COLOR = "#00E5FF30"   # see-through fill of a finished cell
DRAWING_COLOR = "#FFD400"       # the outline being drawn (gold)

HELP_TEXT = ("New selection/add selection point: left click\tDelete selection/Remove selection point: right click\tComplete selection: left double-click\n"
             "Zoom FOV: mouse wheel\tMove FOV: Shift + left-click drag")


# ---------- reading the image ----------

def read_image(path):
    """The image as a 2D numpy array (rows, cols). Only single-channel TIFF images are taken."""
    extension = os.path.splitext(path)[1].lower()
    if extension != ".tif" and extension != ".tiff":
        raise ValueError("This program opens TIFF images (.tif or .tiff) only.")
    # drop axes of length 1, e.g. (1, rows, cols) -> (rows, cols)
    image = np.squeeze(tifffile.imread(path))
    if image.ndim != 2:
        raise ValueError(f"The image has shape {image.shape}. This program takes single-channel 2D images (rows, cols) only.")
    return image


def stretch(plane):
    """Scale an image to 0..1 for the screen: the 1st percentile -> 0, the 99.5th -> 1."""
    plane = plane.astype(np.float32)
    limits = np.percentile(plane, [1, 99.5])
    low = float(limits[0])
    high = float(limits[1])
    if high <= low:
        high = low + 1
    return np.clip((plane - low) / (high - low), 0, 1)


# ---------- outlines -> masks ----------

def outline_pixels(outline, n_rows, n_cols):
    """True for every pixel whose centre is inside the outline (a list of [x, y] corners, x = column, y = row)."""
    corners = np.array(outline, dtype=np.float64)
    inside = np.zeros((n_rows, n_cols), dtype=bool)
    # only the pixels in the rectangle around the outline can be inside it
    left = max(int(np.floor(corners[:, 0].min())), 0)
    right = min(int(np.ceil(corners[:, 0].max())) + 1, n_cols)
    top = max(int(np.floor(corners[:, 1].min())), 0)
    bottom = min(int(np.ceil(corners[:, 1].max())) + 1, n_rows)
    if right <= left or bottom <= top:
        return inside
    grid = np.mgrid[top:bottom, left:right]
    centres = np.column_stack([grid[1].ravel(), grid[0].ravel()])     # [x, y] of every pixel centre
    result = Path(corners).contains_points(centres)
    inside[top:bottom, left:right] = result.reshape(bottom - top, right - left)
    return inside


def outlines_to_masks(outlines, n_rows, n_cols):
    """Cellpose's label image: 0 = background, k + 1 = outline k. Where outlines still overlap (ROIs edited in
    ImageJ can), the earlier outline keeps the pixels."""
    masks = np.zeros((n_rows, n_cols), dtype=np.uint16)
    for k, outline in enumerate(outlines):
        free = outline_pixels(outline, n_rows, n_cols) & (masks == 0)
        masks[free] = k + 1
    return masks


def overlap_pixels(outlines, n_rows, n_cols):
    """How many pixels are inside more than one outline."""
    count = np.zeros((n_rows, n_cols), dtype=np.int32)
    for outline in outlines:
        count += outline_pixels(outline, n_rows, n_cols)
    return int(np.sum(count > 1))


# ---------- outline geometry ----------
# An outline is a list of corners [x, y]. Side i runs from corner i to corner i + 1, and the last side back to corner 0.

def clean_corners(corners):
    """The corners without repeats (a corner at the same place as the one before it, or a last corner on the first)."""
    cleaned = []
    for corner in corners:
        if len(cleaned) > 0:
            last = cleaned[-1]
            if abs(corner[0] - last[0]) < 1e-6 and abs(corner[1] - last[1]) < 1e-6:
                continue
        cleaned.append([float(corner[0]), float(corner[1])])
    while len(cleaned) > 1 and abs(cleaned[-1][0] - cleaned[0][0]) < 1e-6 and abs(cleaned[-1][1] - cleaned[0][1]) < 1e-6:
        cleaned.pop()
    return cleaned


def cross(a, b):
    """The cross product of 2D vectors a and b (positive if b turns left from a)."""
    return a[0] * b[1] - a[1] * b[0]


def side_crossing(p1, p2, q1, q2):
    """How side p1-p2 meets side q1-q2: ["cross", s, t] if they cross at p1 + s (p2 - p1) = q1 + t (q2 - q1) with s and
    t strictly between 0 and 1; ["touch", s, t] if they only touch at an end (or ["touch", -1, -1] if they lie along
    each other); ["none", 0, 0] if they don't meet."""
    r = [p2[0] - p1[0], p2[1] - p1[1]]
    d = [q2[0] - q1[0], q2[1] - q1[1]]
    w = [q1[0] - p1[0], q1[1] - p1[1]]
    r_length = math.hypot(r[0], r[1])
    d_length = math.hypot(d[0], d[1])
    denominator = cross(r, d)
    if abs(denominator) <= TINY * r_length * d_length:
        # parallel: they meet only if they lie on the same line and overlap along it
        if abs(cross(w, r)) > TINY * r_length * max(math.hypot(w[0], w[1]), r_length):
            return ["none", 0, 0]
        r_squared = r[0] * r[0] + r[1] * r[1]
        start = (w[0] * r[0] + w[1] * r[1]) / r_squared
        end = start + (d[0] * r[0] + d[1] * r[1]) / r_squared
        if max(start, end) < -TINY or min(start, end) > 1 + TINY:
            return ["none", 0, 0]
        return ["touch", -1, -1]
    s = cross(w, d) / denominator
    t = cross(w, r) / denominator
    if s < -TINY or s > 1 + TINY or t < -TINY or t > 1 + TINY:
        return ["none", 0, 0]
    if s <= TINY or s >= 1 - TINY or t <= TINY or t >= 1 - TINY:
        return ["touch", s, t]
    return ["cross", s, t]


def crosses_itself(outline):
    """True if two sides of the outline cross or touch, or a corner folds a side back along the one before it."""
    n = len(outline)
    for i in range(n):
        for j in range(i + 1, n):
            p1 = outline[i]
            p2 = outline[(i + 1) % n]
            q1 = outline[j]
            q2 = outline[(j + 1) % n]
            if j == i + 1 or (i == 0 and j == n - 1):
                # neighbouring sides share a corner: they only count if one folds back along the other
                if j == i + 1:
                    first = [p2[0] - p1[0], p2[1] - p1[1]]
                    second = [q2[0] - q1[0], q2[1] - q1[1]]
                else:
                    first = [p1[0] - q1[0], p1[1] - q1[1]]
                    second = [p2[0] - p1[0], p2[1] - p1[1]]
                along = abs(cross(first, second)) <= TINY * math.hypot(first[0], first[1]) * math.hypot(second[0], second[1])
                if along and first[0] * second[0] + first[1] * second[1] < 0:
                    return True
                continue
            if side_crossing(p1, p2, q1, q2)[0] != "none":
                return True
    return False


def is_inside(outline, point):
    """True if the point is inside the outline."""
    return bool(Path(np.array(outline, dtype=np.float64)).contains_point(point))


def distance_to_sides(outline, point):
    """How far the point is from the nearest of the outline's sides, in pixels."""
    n = len(outline)
    shortest = math.inf
    for i in range(n):
        a = outline[i]
        b = outline[(i + 1) % n]
        side = [b[0] - a[0], b[1] - a[1]]
        length_squared = side[0] * side[0] + side[1] * side[1]
        along = 0.0
        if length_squared > 0:
            along = ((point[0] - a[0]) * side[0] + (point[1] - a[1]) * side[1]) / length_squared
        along = min(max(along, 0.0), 1.0)
        nearest = [a[0] + along * side[0], a[1] + along * side[1]]
        shortest = min(shortest, math.hypot(point[0] - nearest[0], point[1] - nearest[1]))
    return shortest


def on_outline(outline, point):
    """True if the point lies on one of the outline's sides (to within 1e-6 pixels)."""
    return distance_to_sides(outline, point) <= 1e-6


def boxes_meet(a, b):
    """True if the rectangles around outlines a and b overlap."""
    a_corners = np.array(a, dtype=np.float64)
    b_corners = np.array(b, dtype=np.float64)
    if a_corners[:, 0].max() < b_corners[:, 0].min() or b_corners[:, 0].max() < a_corners[:, 0].min():
        return False
    if a_corners[:, 1].max() < b_corners[:, 1].min() or b_corners[:, 1].max() < a_corners[:, 1].min():
        return False
    return True


def outline_crossings(a, b):
    """Every point where a side of outline a crosses a side of outline b, as [side of a, how far along it (0..1),
    side of b, how far along it, x, y]. None if the outlines touch anywhere (at a corner, or along a side)."""
    found = []
    n_a = len(a)
    n_b = len(b)
    for i in range(n_a):
        p1 = a[i]
        p2 = a[(i + 1) % n_a]
        for j in range(n_b):
            q1 = b[j]
            q2 = b[(j + 1) % n_b]
            result = side_crossing(p1, p2, q1, q2)
            if result[0] == "touch":
                return None
            if result[0] == "cross":
                s = result[1]
                found.append([i, s, j, result[2], p1[0] + s * (p2[0] - p1[0]), p1[1] + s * (p2[1] - p1[1])])
    return found


def going_inside(outline, positions, points, other):
    """For every crossing k (at points[k], and at positions[k] = side number + how far along it, going round the
    outline): True if the outline goes into the other outline there, False if it comes out of it."""
    n = len(outline)
    order = sorted(range(len(positions)), key=lambda k: positions[k])
    into = []
    for k in range(len(positions)):
        into.append(False)
    for place, k in enumerate(order):
        # halfway to the next crossing or corner along the outline tells whether the outline is inside there
        following = order[(place + 1) % len(order)]
        side = int(positions[k])
        next_point = outline[(side + 1) % n]
        if int(positions[following]) == side and positions[following] > positions[k]:
            next_point = points[following]
        halfway = [(points[k][0] + next_point[0]) / 2, (points[k][1] + next_point[1]) / 2]
        into[k] = is_inside(other, halfway)
    return into


def inside_stretches(positions, into):
    """The stretches of an outline that run inside the other outline, as [crossing, crossing] pairs (smaller number
    first), or None if the crossings going round the outline don't take turns going in and coming out."""
    order = sorted(range(len(positions)), key=lambda k: positions[k])
    stretches = []
    for place, k in enumerate(order):
        following = order[(place + 1) % len(order)]
        if into[k] == into[following]:
            return None
        if into[k]:
            stretches.append([min(k, following), max(k, following)])
    return stretches


def cut_hits_sides(start, end, outline, own_sides):
    """True if the straight cut from start to end meets any side of the outline other than the sides its ends are on."""
    n = len(outline)
    for i in range(n):
        if i in own_sides:
            continue
        if side_crossing(start, end, outline[i], outline[(i + 1) % n])[0] != "none":
            return True
    return False


def cut_stray(start, end, new, old):
    """How far, in pixels, the straight cut from start to end runs outside either outline: the most that the outlines
    can grow beyond what was drawn when they are cut along it."""
    steps = int(math.hypot(end[0] - start[0], end[1] - start[1]) / 0.1) + 1
    stray = 0.0
    for step in range(steps + 1):
        along = step / steps
        point = [start[0] + along * (end[0] - start[0]), start[1] + along * (end[1] - start[1])]
        if not is_inside(new, point):
            stray = max(stray, distance_to_sides(new, point))
        if not is_inside(old, point):
            stray = max(stray, distance_to_sides(old, point))
    return stray


def cut_separates(start, end, new_after, old_after):
    """True if the two outlines, after being cut, lie on opposite sides of the straight cut between them."""
    length = math.hypot(end[0] - start[0], end[1] - start[1])
    if length == 0:
        return False
    # two points just either side of the middle of the cut
    across = [-(end[1] - start[1]) / length * 0.001, (end[0] - start[0]) / length * 0.001]
    middle = [(start[0] + end[0]) / 2, (start[1] + end[1]) / 2]
    one_side = [middle[0] + across[0], middle[1] + across[1]]
    other_side = [middle[0] - across[0], middle[1] - across[1]]
    new_on_one_side = is_inside(new_after, one_side)
    old_on_one_side = is_inside(old_after, one_side)
    if new_on_one_side == is_inside(new_after, other_side) or old_on_one_side == is_inside(old_after, other_side):
        return False
    return new_on_one_side != old_on_one_side


def cut_off(outline, positions, points, into):
    """The outline with every stretch that runs inside another outline replaced by the straight line between the
    crossings at its two ends. The crossings can be with several other outlines."""
    items = []      # [position along the outline, point, "corner" / "in" / "out"], going round the outline
    for i, corner in enumerate(outline):
        items.append([float(i), corner, "corner"])
    for k, position in enumerate(positions):
        what = "out"
        if into[k]:
            what = "in"
        items.append([position, points[k], what])
    items.sort(key=lambda item: item[0])
    # start where the outline is inside the fewest other outlines, so the walk starts outside all of them
    start = 0
    depth = 0
    lowest = 0
    for index, item in enumerate(items):
        if item[2] == "in":
            depth += 1
        if item[2] == "out":
            depth -= 1
        if depth < lowest:
            lowest = depth
            start = index + 1
    result = []
    depth = 0
    for step in range(len(items)):
        item = items[(start + step) % len(items)]
        if item[2] == "corner":
            if depth == 0:
                result.append([item[1][0], item[1][1]])
        else:
            result.append([item[1][0], item[1][1]])
            if item[2] == "in":
                depth += 1
            else:
                depth -= 1
    return result


def split_overlap(new, old, label, n_rows, n_cols):
    """Cut the overlap between a new outline and cell number label's outline, along the straight line between the
    points where the two outlines cross. Returns {"result": "apart" (no overlap), "split" or "refused", "new": the new
    outline after the cut, "old": the cell's outline after the cut, "message": why it was refused, and "positions",
    "points", "into": the crossings along the new outline, for cut_off, and "strayed": True if a cut ran outside the
    overlap}."""
    answer = {"result": "refused", "new": new, "old": old, "message": "", "positions": [], "points": [], "into": [], "strayed": False}
    complicated = f"its overlap with cell {label} cannot be cut with one straight line (let it cross cell {label}'s outline only twice there)"
    if not boxes_meet(new, old):
        answer["result"] = "apart"
        return answer
    crossings = outline_crossings(new, old)
    if crossings is None:
        answer["message"] = f"it touches cell {label}'s outline exactly at a corner or along a side (move that corner a little)"
        return answer
    if len(crossings) == 0:
        if is_inside(old, new[0]):
            answer["message"] = f"it is inside cell {label}"
            return answer
        if is_inside(new, old[0]):
            answer["message"] = f"it goes around cell {label}"
            return answer
        answer["result"] = "apart"
        return answer
    if len(crossings) % 2 == 1:
        answer["message"] = complicated
        return answer
    points = []
    new_positions = []
    old_positions = []
    for crossing in crossings:
        new_positions.append(crossing[0] + crossing[1])
        old_positions.append(crossing[2] + crossing[3])
        points.append([crossing[4], crossing[5]])
    new_into = going_inside(new, new_positions, points, old)
    old_into = going_inside(old, old_positions, points, new)
    new_stretches = inside_stretches(new_positions, new_into)
    old_stretches = inside_stretches(old_positions, old_into)
    if new_stretches is None or old_stretches is None:
        answer["message"] = complicated
        return answer
    # every piece of overlap must lie between one stretch of each outline, joining the same two crossings
    new_stretches.sort()
    old_stretches.sort()
    if new_stretches != old_stretches:
        answer["message"] = complicated
        return answer
    # every cut should run through the overlap without meeting either outline on the way. The straight line across a
    # thin, bent overlap (a crescent) can fall just outside it: that cut is still made if it strays by MAX_CUT_STRAY or less
    strayed_cuts = []
    for stretch_ends in new_stretches:
        first = stretch_ends[0]
        second = stretch_ends[1]
        start = points[first]
        end = points[second]
        halfway = [(start[0] + end[0]) / 2, (start[1] + end[1]) / 2]
        in_new = is_inside(new, halfway) or on_outline(new, halfway)
        in_old = is_inside(old, halfway) or on_outline(old, halfway)
        new_sides = [crossings[first][0], crossings[second][0]]
        old_sides = [crossings[first][2], crossings[second][2]]
        if not in_new or not in_old or cut_hits_sides(start, end, new, new_sides) or cut_hits_sides(start, end, old, old_sides):
            if cut_stray(start, end, new, old) > MAX_CUT_STRAY:
                answer["message"] = complicated
                return answer
            strayed_cuts.append([start, end])
    new_after = clean_corners(cut_off(new, new_positions, points, new_into))
    old_after = clean_corners(cut_off(old, old_positions, points, old_into))
    if len(new_after) < 3 or len(old_after) < 3 or crosses_itself(new_after) or crosses_itself(old_after):
        answer["message"] = complicated
        return answer
    for cut in strayed_cuts:
        if not cut_separates(cut[0], cut[1], new_after, old_after):
            answer["message"] = complicated
            return answer
    old_pixels = int(np.sum(outline_pixels(old_after, n_rows, n_cols)))
    if old_pixels < MIN_CELL_PIXELS:
        answer["message"] = f"cutting the overlap would leave cell {label} with only {old_pixels} pixels (delete cell {label} first if it should go)"
        return answer
    answer["result"] = "split"
    answer["new"] = new_after
    answer["old"] = old_after
    answer["positions"] = new_positions
    answer["points"] = points
    answer["into"] = new_into
    answer["strayed"] = len(strayed_cuts) > 0
    return answer


# ---------- ImageJ ROI sets ----------

def read_rois(path):
    """The outlines in an ImageJ ROI set (.zip), as [outlines, problems]: problems lists the ROIs that are not outlines
    this program can use (lines, points, composite or spline-fitted shapes)."""
    rois = roifile.roiread(path)
    if not isinstance(rois, list):
        rois = [rois]
    area_types = [roifile.ROI_TYPE.POLYGON, roifile.ROI_TYPE.FREEHAND, roifile.ROI_TYPE.TRACED, roifile.ROI_TYPE.RECT, roifile.ROI_TYPE.OVAL]
    outlines = []
    problems = []
    for number, roi in enumerate(rois):
        label = f"ROI {number + 1} ({roi.name})"
        if roi.composite:
            problems.append(label + ": a composite shape")
            continue
        if roi.options & roifile.ROI_OPTIONS.SPLINE_FIT:
            problems.append(label + ": spline-fitted")
            continue
        if roi.roitype not in area_types:
            problems.append(label + ": a " + roi.roitype.name.lower() + ", not an area")
            continue
        outline = []
        for point in roi.coordinates():
            outline.append([float(point[0]) - IMAGEJ_OFFSET, float(point[1]) - IMAGEJ_OFFSET])
        outline = clean_corners(outline)
        if len(outline) < 3:
            problems.append(label + ": fewer than 3 corners")
            continue
        outlines.append(outline)
    return [outlines, problems]


def write_rois(path, outlines):
    """Save the outlines as an ImageJ ROI set (.zip) of polygon ROIs named cell_001, cell_002, ..."""
    rois = []
    for k, outline in enumerate(outlines):
        points = np.array(outline, dtype=np.float64) + IMAGEJ_OFFSET
        roi = roifile.ImagejRoi.frompoints(points, name=f"cell_{k + 1:03d}")
        roi.roitype = roifile.ROI_TYPE.POLYGON
        rois.append(roi)
    # a temporary file first, then swapped in, so a crash while writing never ruins the saved ROI set
    # (mode "w": roifile would otherwise add to an existing zip instead of replacing it)
    temporary = path[:-len(".zip")] + ".tmp.zip"
    if os.path.exists(temporary):
        os.remove(temporary)
    roifile.roiwrite(temporary, rois, mode="w")
    os.replace(temporary, path)


# ---------- the window ----------

class CellOutliner:
    """The outlining window: buttons on top, the image in the middle, a status line at the bottom."""

    def __init__(self, root):
        self.root = root
        # the open image
        self.image = None            # the image as it was read (never changed)
        self.image_path = ""
        self.folder = PROGRAM_FOLDER # the image's folder: the masks and outlines are saved there
        self.name = ""               # the image's file name without extension: every saved file starts with it
        self.n_rows = 0
        self.n_cols = 0
        # the cells
        self.outlines = []           # every cell's outline: a list of [x, y] corners (x = column, y = row)
        self.history = []            # for undo: [earlier outlines, what the change was], the latest last
        self.future = []             # for redo: [later outlines, what the change was], the next one last
        self.masks = None            # the cells as a label image, made again after every change
        self.changed = False         # True if the cells changed since the last save
        self.saved = False           # True if the cells on screen are the ones saved next to the image
        self.drawing = []            # the corners of the outline being drawn
        # moving the view: [mouse x, mouse y (screen pixels), x limits, y limits] where the move started
        self.move_start = None
        # on a Mac ("aqua" windows), a few things differ: Cmd keys, Ctrl + click, and the scroll steps
        self.on_mac = root.tk.call("tk", "windowingsystem") == "aqua"
        self.last_scroll_time = 0.0  # when the view was last zoomed with the wheel (for the Mac's stream of scrolls)
        # what is on screen
        self.picture = None
        self.cell_patches = None     # every finished cell, as one set of shapes
        self.cell_numbers = []       # every finished cell's number
        self.drawing_line = None     # the outline being drawn
        self.build_window()

    def build_window(self):
        """Make the buttons, the help lines, the image and the status line."""
        root = self.root
        root.title("Model Training 2D")
        # top row: files, undo / redo, fit view, the open image
        top = tkinter.Frame(root)
        top.pack(side=tkinter.TOP, fill=tkinter.X)
        tkinter.Button(top, text="Open image (Ctrl + O)", command=self.ask_image).pack(side=tkinter.LEFT)
        tkinter.Button(top, text="Save (Ctrl + S)", command=self.save).pack(side=tkinter.LEFT)
        tkinter.Label(top, text="   ").pack(side=tkinter.LEFT)
        tkinter.Button(top, text="Undo (Ctrl + Z)", command=self.undo).pack(side=tkinter.LEFT)
        tkinter.Button(top, text="Redo (Ctrl + Y)", command=self.redo).pack(side=tkinter.LEFT)
        tkinter.Button(top, text="Fit view (F)", command=self.fit_view).pack(side=tkinter.LEFT)
        self.file_label = tkinter.Label(top, text="No image open")
        self.file_label.pack(side=tkinter.LEFT, padx=10)
        tkinter.Label(root, text=HELP_TEXT, anchor=tkinter.W, justify=tkinter.LEFT).pack(side=tkinter.TOP, fill=tkinter.X)

        # status line at the bottom (packed before the image, so it always stays visible). It has a fixed size of two
        # lines and wraps at the window's width, so that no message can make the window change size
        self.status = tkinter.Label(root, text="Open an image to start", anchor=tkinter.NW, justify=tkinter.LEFT, width=1, height=2)
        self.status.pack(side=tkinter.BOTTOM, fill=tkinter.X)
        self.status.bind("<Configure>", lambda event: self.status.config(wraplength=event.width - 8))

        # the image (the picture fills the whole figure)
        self.figure = Figure(figsize=(9, 7))
        self.axis = self.figure.add_axes([0, 0, 1, 1])
        self.axis.set_axis_off()
        self.canvas = FigureCanvasTkAgg(self.figure, master=root)
        self.canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=True)
        self.canvas.mpl_connect("button_press_event", self.on_press)
        self.canvas.mpl_connect("motion_notify_event", self.on_motion)
        self.canvas.mpl_connect("button_release_event", self.on_release)
        self.canvas.mpl_connect("scroll_event", self.on_scroll)

        # keys and closing the window
        root.bind("<Control-o>", lambda event: self.ask_image())
        root.bind("<Control-s>", lambda event: self.save())
        root.bind("<Control-z>", lambda event: self.undo())
        root.bind("<Control-Z>", lambda event: self.undo())          # Caps Lock on
        root.bind("<Control-y>", lambda event: self.redo())
        root.bind("<Control-Y>", lambda event: self.redo())
        root.bind("<Control-Shift-Z>", lambda event: self.redo())
        if self.on_mac:
            # Mac users press Cmd for these (Ctrl works too)
            root.bind("<Command-o>", lambda event: self.ask_image())
            root.bind("<Command-s>", lambda event: self.save())
            root.bind("<Command-z>", lambda event: self.undo())
            root.bind("<Command-y>", lambda event: self.redo())
            root.bind("<Command-Shift-Z>", lambda event: self.redo())
            root.bind("<Command-Shift-z>", lambda event: self.redo())
        root.bind("<Return>", lambda event: self.finish_drawing())
        root.bind("<Escape>", lambda event: self.cancel_drawing())
        root.bind("<BackSpace>", lambda event: self.remove_last_corner())
        root.bind("<Key-f>", lambda event: self.fit_view())
        root.bind("<Key-F>", lambda event: self.fit_view())
        root.bind("<Home>", lambda event: self.fit_view())
        root.protocol("WM_DELETE_WINDOW", self.on_close)

    def set_status(self, message):
        """Show, in the status line: how many cells there are, whether they are saved, and a message."""
        text = message
        if self.image is not None:
            text = self.count_text() + "    " + message
        self.status.config(text=text)
        self.root.update_idletasks()

    def count_text(self):
        """How many cells there are, whether they are saved, and a note if Cellpose would leave the image out."""
        text = f"{len(self.outlines)} cells"
        if len(self.outlines) == 1:
            text = "1 cell"
        if self.changed:
            text += ", not saved"
        elif self.saved:
            text += ", saved"
        if len(self.outlines) < MIN_TRAIN_MASKS:
            text += f" (fewer than {MIN_TRAIN_MASKS}: train with --min_train_masks 1, or Cellpose leaves this image out)"
        text += "."
        return text

    # ---------- opening an image ----------

    def ask_image(self):
        """Ask for an image file, then open it."""
        path = filedialog.askopenfilename(title="Open an image", initialdir=self.folder, filetypes=[("TIFF images", "*.tif *.tiff"), ("All files", "*.*")])
        if path != "":
            self.open_image(path)

    def open_image(self, path):
        """Open an image, and its saved outlines if it has some."""
        if not self.ok_to_discard():
            return
        try:
            image = read_image(path)
        except Exception as error:
            messagebox.showerror("Cannot open the image", f"{path}\n\n{error}")
            return
        name = os.path.splitext(os.path.basename(path))[0]
        if name.endswith("_masks") or name.endswith("_flows"):
            messagebox.showerror("Cannot open the image", f"{path}\n\nThis is a file Cellpose or this program made from an image. Open the image itself.")
            return
        folder = os.path.dirname(os.path.abspath(path))
        outlines = self.saved_outlines(folder, name)
        if outlines is None:
            return
        self.image = image
        self.image_path = path
        self.folder = folder
        self.name = name
        self.n_rows = image.shape[0]
        self.n_cols = image.shape[1]
        self.outlines = outlines
        self.history = []
        self.future = []
        self.drawing = []
        self.move_start = None
        self.changed = False
        self.saved = len(outlines) > 0
        self.update_masks()
        # the picture, with nothing drawn on it yet, showing the whole image
        self.axis.clear()
        self.axis.set_axis_off()
        self.picture = self.axis.imshow(stretch(image), cmap="gray", vmin=0, vmax=1, interpolation="nearest")
        self.axis.set_autoscale_on(False)
        self.cell_patches = None
        self.cell_numbers = []
        self.drawing_line = None
        self.draw_cells()
        self.fit_view()
        self.file_label.configure(text=f"{os.path.basename(path)}   ({self.n_rows} x {self.n_cols} px, {image.dtype})")
        self.root.title(f"Model Training 2D - {os.path.basename(path)}")
        message = f"Opened {path} with {len(outlines)} saved cells"
        shared = overlap_pixels(outlines, self.n_rows, self.n_cols)
        if shared > 0:
            message += f". {shared} pixels are inside more than one outline (the lower-numbered cell gets them)"
        self.set_status(message)

    def saved_outlines(self, folder, name):
        """The outlines saved next to this image ([] if none), or None if the user cancels opening."""
        rois_path = os.path.join(folder, name + "_RoiSet.zip")
        if not os.path.exists(rois_path):
            return []
        try:
            read = read_rois(rois_path)
        except Exception as error:
            messagebox.showerror("Cannot read the saved outlines", f"{rois_path}\n\n{error}")
            return None
        outlines = read[0]
        problems = read[1]
        if len(problems) > 0:
            listing = "\n".join(problems)
            use_rest = messagebox.askokcancel("Some ROIs cannot be used", f"{rois_path} has {len(problems)} ROIs this program cannot use:\n\n{listing}\n\nOK: open the image without them (saving replaces the ROI set, so they will be gone from it).\nCancel: don't open the image.")
            if not use_rest:
                return None
        return outlines

    # ---------- the cells on screen ----------

    def draw_cells(self):
        """Show every finished cell: its outline, a see-through fill and its number."""
        if self.cell_patches is not None:
            self.cell_patches.remove()
        for number in self.cell_numbers:
            number.remove()
        self.cell_numbers = []
        shapes = []
        for k, outline in enumerate(self.outlines):
            corners = np.array(outline)
            shapes.append(corners)
            middle = corners.mean(axis=0)
            self.cell_numbers.append(self.axis.text(middle[0], middle[1], str(k + 1), color=CELL_EDGE_COLOR, fontsize=8, ha="center", va="center"))
        self.cell_patches = PolyCollection(shapes, facecolors=CELL_FILL_COLOR, edgecolors=CELL_EDGE_COLOR, linewidths=1)
        self.axis.add_collection(self.cell_patches, autolim=False)

    def draw_drawing(self, cursor=None):
        """Show the outline being drawn: its corners, and a line on to the mouse."""
        if self.image is None:
            return
        xs = []
        ys = []
        for corner in self.drawing:
            xs.append(corner[0])
            ys.append(corner[1])
        if cursor is not None and len(self.drawing) > 0:
            xs.append(cursor[0])
            ys.append(cursor[1])
        if self.drawing_line is None:
            self.drawing_line = self.axis.plot(xs, ys, color=DRAWING_COLOR, linewidth=1.5, marker="o", markersize=3)[0]
        else:
            self.drawing_line.set_data(xs, ys)
        self.canvas.draw_idle()

    # ---------- zooming and moving the view ----------

    def fit_view(self):
        """Show the whole image (F, Home or the Fit view button)."""
        if self.image is None:
            return
        self.axis.set_xlim(-0.5, self.n_cols - 0.5)
        self.axis.set_ylim(self.n_rows - 0.5, -0.5)
        self.canvas.draw_idle()

    def set_view(self, left, right, top, bottom):
        """Show image columns left..right and rows top..bottom: kept inside the image, and never closer than
        MIN_VIEW_PIXELS pixels across (zooming out past the whole image shows the whole image)."""
        width = right - left
        height = bottom - top
        if width >= self.n_cols or height >= self.n_rows:
            self.fit_view()
            return
        if width < MIN_VIEW_PIXELS:
            # too close: grow the view around its centre, keeping its shape
            factor = MIN_VIEW_PIXELS / width
            centre_x = (left + right) / 2
            centre_y = (top + bottom) / 2
            width = width * factor
            height = height * factor
            left = centre_x - width / 2
            right = centre_x + width / 2
            top = centre_y - height / 2
            bottom = centre_y + height / 2
        # slide the view back inside the image
        if left < -0.5:
            right = right + (-0.5 - left)
            left = -0.5
        if right > self.n_cols - 0.5:
            left = left - (right - (self.n_cols - 0.5))
            right = self.n_cols - 0.5
        if top < -0.5:
            bottom = bottom + (-0.5 - top)
            top = -0.5
        if bottom > self.n_rows - 0.5:
            top = top - (bottom - (self.n_rows - 0.5))
            bottom = self.n_rows - 0.5
        self.axis.set_xlim(left, right)
        # rows grow downwards on screen
        self.axis.set_ylim(bottom, top)
        self.canvas.draw_idle()

    def on_scroll(self, event):
        """Mouse wheel on the image: zoom in (wheel up) or out (wheel down), keeping the pixel under the mouse in place."""
        if self.image is None or event.inaxes is not self.axis or event.xdata is None:
            return
        step = event.step
        if self.on_mac:
            # matplotlib divides each scroll by 120 (the size of one wheel step on Windows), but a Mac sends much
            # smaller scrolls, and a trackpad sends a stream of them. So on a Mac, every scroll is one zoom step, at
            # most one per MAC_SCROLL_INTERVAL seconds. (Not tried on a Mac yet: if zooming there is too fast or too
            # slow, change MAC_SCROLL_INTERVAL.)
            now = time.monotonic()
            if now - self.last_scroll_time < MAC_SCROLL_INTERVAL:
                return
            self.last_scroll_time = now
            if step > 0:
                step = 1
            elif step < 0:
                step = -1
        if step == 0:
            return
        factor = ZOOM_STEP ** (-step)
        x_limits = self.axis.get_xlim()
        y_limits = self.axis.get_ylim()
        left = x_limits[0]
        right = x_limits[1]
        top = y_limits[1]
        bottom = y_limits[0]
        x = event.xdata
        y = event.ydata
        self.set_view(x - (x - left) * factor, x + (right - x) * factor, y - (y - top) * factor, y + (bottom - y) * factor)

    def move_view(self, event):
        """Middle-drag or Shift + left-drag: the image follows the mouse."""
        start = self.move_start
        box = self.axis.bbox
        # image pixels per screen pixel, then how far the mouse moved in image pixels
        x_scale = (start[2][1] - start[2][0]) / box.width
        y_scale = (start[3][1] - start[3][0]) / box.height
        shift_x = (event.x - start[0]) * x_scale
        shift_y = (event.y - start[1]) * y_scale
        left = start[2][0] - shift_x
        right = start[2][1] - shift_x
        bottom = start[3][0] - shift_y
        top = start[3][1] - shift_y
        self.set_view(left, right, top, bottom)

    # ---------- the mouse ----------

    def mouse_point(self, event):
        """The mouse position as [x, y] in image pixels, kept inside the image. It is not rounded, so a corner
        practically never lands exactly on a pixel centre (where it would be unclear which side the pixel is on)."""
        x = min(max(float(event.xdata), -0.5), self.n_cols - 0.5)
        y = min(max(float(event.ydata), -0.5), self.n_rows - 0.5)
        return [x, y]

    def on_press(self, event):
        """Mouse button down: start moving the view, add or take back a corner, finish the outline, or delete a cell."""
        if self.image is None or event.inaxes is not self.axis:
            return
        # middle button, or Shift + left button: move the view
        if event.button == 2 or (event.button == 1 and "shift" in event.modifiers):
            self.move_start = [event.x, event.y, self.axis.get_xlim(), self.axis.get_ylim()]
            return
        point = self.mouse_point(event)
        button = event.button
        # on a Mac, Ctrl + click is a right-click
        if self.on_mac and button == 1 and "ctrl" in event.modifiers:
            button = 3
        if button == 3:
            # right-click: take back the last corner of the outline being drawn, or else delete the cell under the mouse
            if len(self.drawing) > 0:
                self.remove_last_corner()
            else:
                self.delete_cell_at(point)
            return
        if button != 1:
            return
        # the second click of a double-click finishes the outline (the first one added a corner)
        if event.dblclick:
            if len(self.drawing) > 0:
                self.finish_drawing()
            return
        # a click on the first corner finishes the outline, any other click adds a corner
        if len(self.drawing) >= 3 and self.near_first_corner(event):
            self.finish_drawing()
            return
        self.drawing.append(point)
        self.draw_drawing(point)
        self.set_status(f"Drawing: {len(self.drawing)} corners")

    def on_motion(self, event):
        """Mouse moved: move the view, or show the outline's next side."""
        if self.move_start is not None:
            self.move_view(event)
            return
        if self.image is None or event.inaxes is not self.axis or event.xdata is None:
            return
        if len(self.drawing) > 0:
            self.draw_drawing(self.mouse_point(event))

    def on_release(self, event):
        """Mouse button up: stop moving the view."""
        if self.move_start is not None:
            self.move_start = None

    def near_first_corner(self, event):
        """True if the mouse is within CLOSE_DISTANCE screen pixels of the first corner."""
        first = self.axis.transData.transform(self.drawing[0])
        distance = np.hypot(event.x - first[0], event.y - first[1])
        return distance <= CLOSE_DISTANCE

    # ---------- changing the cells ----------

    def finish_drawing(self):
        """Turn the outline being drawn into a cell, cutting any overlap with other cells. If it cannot be added, it
        stays on screen with the reason in the status line, to be corrected (right-click) or dropped (Escape)."""
        if len(self.drawing) == 0:
            return
        try_again = ". Right-click takes back corners, Esc drops the outline"
        new_outline = clean_corners(self.drawing)
        if len(new_outline) < 3:
            self.set_status("Not added: a cell needs at least 3 corners")
            return
        if crosses_itself(new_outline):
            self.set_status("Not added: the outline crosses itself" + try_again)
            return
        # cut the overlaps with the other cells (on new copies of the outlines, so undo has the old ones). Every cell is
        # compared with the outline as drawn, and all the cuts are made at the end: a cut ends on the border of the cell
        # it was made in, so an outline already cut would touch any neighbour that shares that border
        outlines = list(self.outlines)
        cut_cells = []
        positions = []
        points = []
        into = []
        strayed = False
        for k, old_outline in enumerate(outlines):
            result = split_overlap(new_outline, old_outline, k + 1, self.n_rows, self.n_cols)
            if result["result"] == "refused":
                self.set_status("Not added: " + result["message"] + try_again)
                return
            if result["result"] == "split":
                outlines[k] = result["old"]
                cut_cells.append(str(k + 1))
                positions += result["positions"]
                points += result["points"]
                into += result["into"]
                if result["strayed"]:
                    strayed = True
        if len(cut_cells) > 0:
            new_outline = clean_corners(cut_off(new_outline, positions, points, into))
            if len(new_outline) < 3 or crosses_itself(new_outline):
                self.set_status("Not added: cutting its overlaps with cells " + ", ".join(cut_cells) + " leaves no clean outline" + try_again)
                return
        if strayed:
            # a cut that ran outside its overlap makes outlines a little larger: they must not grow into a third cell
            after_cuts = list(outlines)
            after_cuts.append(new_outline)
            if overlap_pixels(after_cuts, self.n_rows, self.n_cols) > overlap_pixels(self.outlines, self.n_rows, self.n_cols):
                self.set_status("Not added: cutting its overlaps with cells " + ", ".join(cut_cells) + " would push an outline into a neighbouring cell" + try_again)
                return
        masks = outlines_to_masks(outlines, self.n_rows, self.n_cols)
        count = int(np.sum(outline_pixels(new_outline, self.n_rows, self.n_cols) & (masks == 0)))
        if count < MIN_CELL_PIXELS:
            self.set_status(f"Not added: it covers only {count} pixels outside other cells (at least {MIN_CELL_PIXELS} needed)" + try_again)
            return
        message = f"Cell {len(outlines) + 1} added ({count} pixels)"
        if len(cut_cells) == 1:
            message += f", overlap with cell {cut_cells[0]} cut"
        if len(cut_cells) > 1:
            message += ", overlaps with cells " + ", ".join(cut_cells) + " cut"
        self.remember(message)
        outlines.append(new_outline)
        self.outlines = outlines
        self.drawing = []
        self.draw_drawing()
        self.after_change(message)

    def delete_cell_at(self, point):
        """Delete the cell that owns the pixel under the mouse."""
        row = min(max(int(round(point[1])), 0), self.n_rows - 1)
        col = min(max(int(round(point[0])), 0), self.n_cols - 1)
        label = int(self.masks[row, col])
        if label == 0:
            return
        message = f"Cell {label} deleted"
        self.remember(message)
        outlines = []
        for k, outline in enumerate(self.outlines):
            if k != label - 1:
                outlines.append(outline)
        self.outlines = outlines
        self.after_change(message)

    def remember(self, what):
        """Keep the cells as they are now, so the change about to be made (described by what) can be undone. A new
        change ends what could be redone."""
        self.history.append([self.outlines, what])
        self.future = []

    def undo(self):
        """Ctrl+Z (or Undo): take back the last corner of the outline being drawn, or else the last change."""
        if len(self.drawing) > 0:
            self.remove_last_corner()
            return
        if len(self.history) == 0:
            self.set_status("Nothing to undo")
            return
        step = self.history.pop()
        self.future.append([self.outlines, step[1]])
        self.outlines = step[0]
        self.after_change("Undone: " + step[1])

    def redo(self):
        """Ctrl+Y or Ctrl+Shift+Z (or Redo): make the last undone change again."""
        if len(self.drawing) > 0:
            self.set_status("Finish the outline being drawn (or drop it with Esc) before redoing")
            return
        if len(self.future) == 0:
            self.set_status("Nothing to redo")
            return
        step = self.future.pop()
        self.history.append([self.outlines, step[1]])
        self.outlines = step[0]
        self.after_change("Redone: " + step[1])

    def after_change(self, message):
        """After the cells changed: make the masks again, redraw, and say what happened."""
        self.changed = True
        self.update_masks()
        self.draw_cells()
        self.canvas.draw_idle()
        self.set_status(message)

    def update_masks(self):
        """Make the label image from the outlines (cell k + 1 = outline k)."""
        self.masks = outlines_to_masks(self.outlines, self.n_rows, self.n_cols)

    def cancel_drawing(self):
        """Escape: drop the outline being drawn."""
        if len(self.drawing) == 0:
            return
        self.drawing = []
        self.draw_drawing()
        self.set_status("Outline dropped")

    def remove_last_corner(self):
        """Right-click, Backspace or Ctrl+Z while drawing: take back the last corner (taking back the only corner drops
        the outline)."""
        if len(self.drawing) == 0:
            return
        self.drawing.pop()
        self.draw_drawing()
        if len(self.drawing) == 0:
            self.set_status("Outline dropped")
            return
        self.set_status(f"Drawing: {len(self.drawing)} corners")

    # ---------- saving ----------

    def save(self):
        """Save the masks and the outlines (as an ImageJ ROI set) next to the image. The image itself is not changed."""
        if self.image is None:
            return
        masks_path = os.path.join(self.folder, self.name + "_masks.tif")
        rois_path = os.path.join(self.folder, self.name + "_RoiSet.zip")
        flows_path = os.path.join(self.folder, self.name + "_flows.tif")
        try:
            # the cells, in Cellpose's label format
            tifffile.imwrite(masks_path, self.masks)
            # Cellpose keeps the flows it works out from the masks in <name>_flows.tif, and once every image has one
            # it trains on those instead of the masks: delete this image's, so training uses the new masks
            if os.path.exists(flows_path):
                os.remove(flows_path)
            # the outlines, for ImageJ and for opening the image here again (an empty ROI set is no file at all)
            if len(self.outlines) > 0:
                write_rois(rois_path, self.outlines)
            elif os.path.exists(rois_path):
                os.remove(rois_path)
        except Exception as error:
            messagebox.showerror("Cannot save", f"Saving next to {self.image_path} did not work:\n\n{error}\n\nThe cells are still here: check that the folder can be written to, then save again.")
            self.set_status(f"Not saved: {error}")
            return
        self.changed = False
        self.saved = True
        self.set_status(f"Saved {self.name}_masks.tif and {self.name}_RoiSet.zip next to the image")

    def ok_to_discard(self):
        """True if there are no unsaved cells, or the user chose to save them (and saving worked) or let them go."""
        if not self.changed:
            return True
        answer = messagebox.askyesnocancel("Unsaved cells", "Save the cells first?")
        if answer is None:
            return False
        if answer:
            self.save()
            # if saving did not work, stay on this image
            return not self.changed
        return True

    def on_close(self):
        """Closing the window: offer to save first."""
        if self.ok_to_discard():
            self.close_window()

    def close_window(self):
        """Close the window. Redraws still waiting to happen are cancelled first, so they don't run after the window
        is gone (which prints 'invalid command name' errors). They are cancelled in Tk itself: root.after_cancel would also
        delete the commands of other widgets, and those widgets would then fail to delete them again when destroyed."""
        for after_id in self.root.tk.eval("after info").split():
            self.root.tk.call("after", "cancel", after_id)
        self.root.destroy()


def main():
    """Open the outlining window (and the image given on the command line, if any)."""
    root = tkinter.Tk()
    app = CellOutliner(root)
    if len(sys.argv) > 1:
        app.open_image(sys.argv[1])
    root.mainloop()


if __name__ == "__main__":
    main()
