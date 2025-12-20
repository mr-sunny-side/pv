import sys
import struct

L_WIDTH = 15
R_WIDTH = 15

def read_bmp(file_name):
    try:
        with open(file_name, 'rb') as f:

            file_header = f.read(14)
            # \で改行を明確にできる
            file_type, file_size, pixel_offset = \
                struct.unpack('<2sIxxxxI', file_header)
            if file_type != b'BM':
                return None

            info_header = f.read(40)
            width, hight, planes, depth, compression = \
                struct.unpack('<xxxxiiHHI', info_header)
            if planes != 0x01:
                return None

            return {
                'file_type': file_type,
                'file_size': file_size,
                'width': width,
                'hight': hight,
                'depth': depth,
                'compression': compression,
                'pixel_offset': pixel_offset,
            }


    except FileNotFoundError as e:
        print(e)
        return None
    except Exception as e:
        print(e)
        return None

def print_result(title, label, value):
    if title:
        title = title.center(30, '=')
        print(title)

    print(f"{label:<{L_WIDTH}}{value:>{R_WIDTH}}")

def main():

    if len(sys.argv) != 2:
        print("Argument error", file=sys.stderr)
        print("Usage: [this file] [.bmp]", file=sys.stderr)
        return 1

    file_name = sys.argv[1]

    header_info = read_bmp(file_name)
    if header_info is None:
        print("read_bmp returned None", file=sys.stderr)
        return 1

    print_result(' BMP File Information ', 'File size: ', f"{header_info['file_size']} bytes")
    print_result(None, 'Image size: ', f"{header_info['width']} * {header_info['hight']} pixels")
    print_result(None, 'Bit per pixels: ', header_info['depth'])

    if header_info['compression'] == 0x00:
        print_result(None, 'Compression: ', '0 (0=None)')
    else:
        print_result(None, 'Compression: ', header_info['compression'])

    print_result(None, 'Data offset: ', header_info['pixel_offset'])
    print()

    return 0

"""
=== BMP File Information ===
File size: 310 bytes
Image size: 8 x 8 pixels
Bits per pixel: 24
Compression: 0 (0=none)
Data offset: 54 bytes

"""

if __name__ == '__main__':
    sys.exit(main())
