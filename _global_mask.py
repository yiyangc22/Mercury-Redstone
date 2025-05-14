"""Global Mask Generation Test"""

import os
import pandas as pd
from PIL import Image

# Constants
INPUT_FOLDER = "D:\\Temp\\_latest\\Mask Images"
INPUT_AFFIX = '.png'
COORDINATE_FILE = "D:\\Temp\\_latest\\_coordinates.csv"
OUTPUT_FILE = "D:\\Temp\\_latest\\stitched_output.png"
IMAGE_SIZE_PX = 1024
MICRONS_PER_IMAGE = 366.0  # 1024 px = 366.0 µm
PIXELS_PER_MICRON = IMAGE_SIZE_PX / MICRONS_PER_IMAGE

def read_coordinates(csv_file):
    # read .csv, save xy coordinates in list, and print
    csv = pd.read_csv(csv_file).values.tolist()
    coords = []
    for row in csv:
        # invert x (row[1]) or y (row[2]) axis here
        coords.append([row[1], row[2]])
    # create regions in matplotlib based on the coordinates
    return coords

def main():
    # Get PNG files sorted by name
    image_files = sorted([f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(INPUT_AFFIX)])
    coordinates = read_coordinates(COORDINATE_FILE)

    if len(image_files) != len(coordinates):
        raise ValueError("Mismatch between number of images and coordinate entries.")

    # Convert coordinates to pixel units
    pixel_coords = []
    for x, y in coordinates:
        pixel_coords.append([-round(x * PIXELS_PER_MICRON), round(y * PIXELS_PER_MICRON)])

    # Determine the bounds of the final canvas
    min_x = min(x for x, y in pixel_coords)
    min_y = min(y for x, y in pixel_coords)
    max_x = max(x for x, y in pixel_coords)
    max_y = max(y for x, y in pixel_coords)
    width = max_x - min_x + IMAGE_SIZE_PX
    height = max_y - min_y + IMAGE_SIZE_PX

    # Subtract min x and y from all coordinates
    for coord in pixel_coords:
        coord[0] -= min_x
        coord[1] -= min_y

    # Create blank output image in 'P' mode with 8-bit depth
    output_image = Image.new('P', (width, height), color=(255,255,255))

    for i, coords in enumerate(pixel_coords):
        img_path = os.path.join(INPUT_FOLDER, image_files[i])
        img = Image.open(img_path).convert('P')
        paste_x = coords[0]
        paste_y = coords[1]
        output_image.paste(img, (paste_x, paste_y))

    # Flip the image vertically and horizontally
    output_image = output_image.transpose(method=Image.Transpose.FLIP_LEFT_RIGHT)
    output_image = output_image.transpose(method=Image.Transpose.FLIP_TOP_BOTTOM)


    # Save the result
    output_image.save(OUTPUT_FILE)
    print(f"Saved stitched image as {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
