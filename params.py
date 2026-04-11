"""
Params: experiment-wide parameter control, project version 1.25 (with python 3.9).
"""

import os
from datetime import date

# desktop path (suggested, can change in ctk window)
PARAMS_DTP = os.path.join(os.path.expanduser("~"), "Desktop")
# default experiment folder path (suggested, can change in ctk window)
PARAMS_EXP = os.path.join(PARAMS_DTP, f"latest_{date.today()}")
# default multichannel folder name (fixed)
PARAMS_MCI = "image_multichannel"
# default mask image folder name (fixed)
PARAMS_MSK = "image_mask"
# default laser image folder name (fixed)
PARAMS_LSR = "image_laser"
# default laser cleave map/coordinate folder name (fixed)
PARAMS_MAP = "image_cleave_map"
# default multichannel image coordinate file name (fixed)
PARAMS_PLN = "coord_planned.csv"
PARAMS_CRD = "coord_recorded.csv"
# default global mask file name (fixed)
PARAMS_GLB = "image_mask_global.png"
# default scan region center coordinate file name (fixed)
PARAMS_SCT = "coord_scan_center.csv"
# default scan region bit scheme/string file name (fixed)
PARAMS_BIT = "config_bit_scheme.csv"
# default temporary laser mask file name (fixed)
PARAMS_TMP = "image_mask_tmp.png"
# default version marker (fixed)
PARAMS_VER = "1.25"
