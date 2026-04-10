
# Mercury-Redstone (v1.24, Python 3.9.13)
> **Important!** This version is only compatable with [NI LabVIEW 2022 Q3 (64-bits) Professional](https://www.ni.com/en/support/downloads/software-products/download.labview.html?) running on Windows 10.

**Mercury-Redstone** is a software prgram for controlling a photonic-indexing sequencing (pi-seq) microscope, which is currently under development in [Luo Lab at UCLA](https://luogenomics.github.io/). The complete program has 2 parts:
- *LabVIEW programs* - NOT in this repository, uses [NI LabVIEW 2022 Q3 (64-bits) Professional](https://www.ni.com/en/support/downloads/software-products/download.labview.html?srsltid=AfmBOoqFKqWzXdRyj8mGl-pJSyPNZdrEf62go6jATzivkT-w3GGZH7Um#570679).
- *Python programs* - what's in this repository, uses [Python 3.9.13](https://www.python.org/downloads/release/python-3913/).

You can run Python programs independently on any computer, given you have an experiment folder generated from the pi-seq microscope. Future versions of this repository may included LabVIEW programs. **This repository is intended for documentation/internal uses only**.

## How to use this repository
First, use `mercury.yml` to install conda environment for this project. This version (1.24) does not currently use Cellpose (version 3.1.1.1) as included in the yml file, but future versions (1.25+) may require this version of Cellpose.

If you only need to run Python programs, download this repository and run the `mercury_XX.py` files. Within each of these files, run functions named `mercury_XX()`. You don't need to put this repository or its files into an experiment folder in order to run the program.

If you're running the programs together with LabVIEW programs on a pi-seq microscope computer, download and extract this repository into `..\\MAIN_SCRIBE_CONTROL_2022_Update Folder (1.24)\\_Python\\Mercury 1.24`, where `MAIN_SCRIBE_CONTROL_2022_Update Folder (1.24)` is your LabVIEW project folder.

## Files in this repository
```
Mercury-Redstone-1.24         # (this repository)
 ├─ ShearValve_Module.py       # shear valve control functions
 ├─ default_calibration.yaml   # default laser calibration preset, stored as yaml
 ├─ imagej_mask_v124_366px.txt # ImageJ script for watershed segmentation (366px)
 ├─ imagej_mask_v124_732px.txt # ImageJ script for watershed segmentation (732px)
 ├─ mercury.yml                # conda env for project mercury
 ├─ mercury_00.py              # for mask calibration
 ├─ mercury_01.py              # for tissue imaging
 ├─ mercury_02.py              # for making submasks and bit strings
 ├─ mercury_02_copy.py         # mercury_02.py modified for running 732px masks
 ├─ mercury_03.py              # for coordinating laser and fluidics
 ├─ mercury_03_copy.py         # mercury_03.py modified for running 732px masks
 ├─ mercury_04.py              # for previewing and stitching images
 ├─ mercury_05.py              # for single fluidic procedures
 ├─ mercury_06.py              # for single laser procedures
 ├─ readme.md                  # (this file)
```
## Files in a typical experiment folder
```
Experiment Folder               # (name can vary based on user input)
 ├─ image_cleave_map             # folder, contains global masks for laser
 │   ├─ Round 0.csv               # list of all submasks lasered in round 0
 │   ├─ Round 0.png               # global mask for all submasks in round 0
 │   ├─ Round 1.csv               # list of all submasks lasered in round 1
 │   ├─ Round 1.png               # global mask for all submasks in round 1
 │  ...                             ...
 │
 ├─ image_laser                  # folder, contains laser cleavage images
 │   ├─ 1000_1000_F001_Z001.tif   # image 1000, 1st laser image taken
 │   ├─ 1000_1001_F001_Z001.tif   # image 1001, 2nd laser image taken
 │   ├─ 1000_1002_F001_Z001.tif   # image 1002, 3rd laser image taken
 │   ├─ 1000_1003_F001_Z001.tif   # image 1003, 4th laser image taken
 │  ...                             ...
 │
 ├─ image_mask                   # folder, contains mask images
 │   ├─ 1000_MC_F001_Z001.png     # mask 1000, of multichannel image 1000
 │   ├─ 1001_MC_F001_Z001.png     # mask 1001, of multichannel image 1001
 │   ├─ 1002_MC_F001_Z001.png     # mask 1002, of multichannel image 1002
 │   ├─ 1003_MC_F001_Z001.png     # mask 1003, of multichannel image 1003
 │  ...
 │
 ├─ image_multichannel           # folder, contains multichannel images
 │   ├─ 1000_MC_F001_Z001.tif     # image 1001, 1st multichannel image taken
 │   ├─ 1001_MC_F001_Z001.tif     # image 1002, 1st multichannel image taken
 │   ├─ 1002_MC_F001_Z001.tif     # image 1003, 1st multichannel image taken
 │   ├─ 1003_MC_F001_Z001.tif     # image 1004, 1st multichannel image taken
 │  ...
 │
 ├─ config_bit_scheme.csv        # list of all submasks and their bit string
 ├─ coord_planned.csv            # multichannel image coordinates, planned
 ├─ coord_recorded.csv           # multichannel image coordinates, recorded
 ├─ coord_scan_center.csv        # coordinates for laser cleave locations
 ├─ image_mask_global.png        # image, global mask of all segmented cells
 ├─ image_mask_tmp.png           # image, temporary mask for laser cleaving
```
> **Important!** Multichannel and mask images of the same number are for the same area, but not for laser images of the same number. If you'd like to overlay laser images onto masks, use `mercury_04.py`.
>
Additionally, if an experiment used over 21 ports, it will be split into 2 parts. Each part will be represented by a separate experiment folder with the same structure as the above. While the two folders do share the same set of multichannel images, global masks, and coordinates, do not try to combine them via copying and pasting (as files with the same name will be overwritten). **Future versions of this repository may depricate the use of splitting experiment folders.**

## Files for post-experiment analyses
The most important file for any spatial analysis is the `config_bit_scheme.csv`. It contains 8 columns of information about every submasking area. The first 6 columns represent the coordinates of this area:
|x (um)|y (um)|w (px)|n (px)|e (px)|s (px)|
|---|---|---|---|---|---|
|**x coordinate**<br>*on microscope*|**y coordinate**<br>*on microscope*|**west bound**<br>*on global mask*|**north bound**<br>*on global mask*|**east bound**<br>*on global mask*|**south bound**<br>*on global mask*|
>
The last 2 columns represent the barcoding sequence this area will receive:
|index (port indexes)||bit (bit string)|
|---|---|---|
|A list of port indexes (port numbers), each represents a concatenation||A list (string) of 0s and 1s, each represents if this area will be barcoded in thats specific round|
|e.g. `[0,1,2,5]` = this area will receive barcodes from ports `0`, `1`, `2`, and `5`, respectively||e.g. `[1,1,1,0,0,1,0,...]` = this area will be barcoded in rounds `0`, `1`, `2`, and `5`, respectively|
> **Important!** In this version, `I01-I02-I03-I06` corresponds to `[0,1,2,5]`, not `[1,2,3,6]`.
>
In addition to `config_bit_scheme.csv`, you can use the `map_spatial_subarea` function in `mercury_02.py` to overlay scan areas and submasks onto a stitched background of mask images.

## Summary of changes in version 1.24
- Added support for mask calibration (`mercury_00.py`)
- Added support for grid submasking previewing function (`mercury_02.py`).
- Added this readme file for documentation purposes.

> **Note:** Experiment folders using this version (1.24) is incompatable with other 0.01 versions (e.g. version 1.25).
