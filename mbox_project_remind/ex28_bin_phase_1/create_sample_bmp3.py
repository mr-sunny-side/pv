#!/usr/bin/env python3

import struct

def create_bmp(filename, width, height, pixels):
    """
    Create a BMP file with given dimensions and pixel data
    pixels: list of (R, G, B) tuples
    """
    # BMP Header
    file_size = 54 + (width * height * 3)
    reserved = 0
    offset = 54

    # DIB Header (BITMAPINFOHEADER)
    dib_header_size = 40
    planes = 1
    bits_per_pixel = 24
    compression = 0
    image_size = width * height * 3
    x_pixels_per_meter = 2835
    y_pixels_per_meter = 2835
    colors_used = 0
    important_colors = 0

    with open(filename, 'wb') as f:
        # BMP Header
        f.write(b'BM')
        f.write(struct.pack('<I', file_size))
        f.write(struct.pack('<I', reserved))
        f.write(struct.pack('<I', offset))

        # DIB Header
        f.write(struct.pack('<I', dib_header_size))
        f.write(struct.pack('<i', width))
        f.write(struct.pack('<i', height))
        f.write(struct.pack('<H', planes))
        f.write(struct.pack('<H', bits_per_pixel))
        f.write(struct.pack('<I', compression))
        f.write(struct.pack('<I', image_size))
        f.write(struct.pack('<i', x_pixels_per_meter))
        f.write(struct.pack('<i', y_pixels_per_meter))
        f.write(struct.pack('<I', colors_used))
        f.write(struct.pack('<I', important_colors))

        # Pixel data (bottom to top, BGR format)
        for y in range(height - 1, -1, -1):
            for x in range(width):
                idx = y * width + x
                r, g, b = pixels[idx]
                f.write(struct.pack('BBB', b, g, r))

# Create asymmetric pattern
width, height = 10, 10
pixels = []

for y in range(height):
    for x in range(width):
        # Asymmetric color pattern
        if x < 3 and y < 4:
            color = (255, 0, 0)  # Red
        elif x > 6 and y > 5:
            color = (0, 0, 255)  # Blue
        elif x == y:
            color = (0, 255, 0)  # Green
        elif x + y == 9:
            color = (255, 255, 0)  # Yellow
        else:
            color = (128, 128, 128)  # Gray
        pixels.append(color)

create_bmp('/tmp/asymmetric_10x10.bmp', width, height, pixels)
print("Asymmetric 10x10 BMP created successfully")
