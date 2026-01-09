#!/usr/bin/env python3

import sys
import struct

def process_read(f):
    data = f.read(12) if f else None

    if data is None or len(data) != 12:
        print(f"Cannot read {f}")
        return None

    chunk_id, chunk_size, format = struct.unpack('<4sI4s', data)

    if chunk_id != b'RIFF' or format != b'WAVE':
        print("This file is not WAV", file=sys.stderr)
        print(f"Chunk ID: {chunk_id}", file=sys.stderr)
        print(f"Format: {format}", file=sys.stderr)
        return None

    return {
            'chunk_id': chunk_id.decode('ascii'),   # バイト型なのでstr()ではなく、.decode()しないとb'RIFF'になる
            'chunk_size': chunk_size,               #これはint型なのでデコードしなくていい
            'format': format.decode('ascii')
    }

def print_result(title, riff):
    if title:
        title = title.center(20, '=')
        print(title)
    if isinstance(riff, dict):
        for label, value in riff.items():
            print(f"{label}: {value}")

"""
=== RIFF Header ===
Chunk ID: RIFF
Chunk size: 90660 bytes
Format: WAVE

✓ This is a valid WAV file.

"""

def main():
    if len(sys.argv) != 2:
        print("Argument error", file=sys.stderr)
        return -1

    file_name = sys.argv[1]
    try:
        with open (file_name, "rb") as f:
            riff = process_read(f)
            if riff is None:
                return 1

        print_result(" RIFF Header ", riff)
        print("✓ This is a valid WAV file.")

        return 0


    except FileNotFoundError as e:
        print(e)
        return 1
    except Exception as e:
        print(e)
        return 1


if __name__ == '__main__':
    sys.exit(main())
