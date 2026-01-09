#!/usr/bin/env python3

import sys
import struct

"""
=== WAV File Information ===
Audio format: 1 (PCM)
Channels: 1 (Mono)
Sample rate: 44100 Hz
Bits per sample: 16
Data size: 88200 bytes
Duration: 1.00 seconds

 - RIFF, WAVEでない場合エラーを出力
 - 標準fmtより長い場合、残りをスキップ
 - 不明なチャンクを丸ごとスキップ
 ※ バイト型はとstr型の違いに注意
 ※ 戻り値Noneはエラーの原因になるので、確実なエラー出力などで使用

"""

def process_read(f):

    # 検証用の最初の読取
    tmp = f.read(8) if f else None
    if not tmp or len(tmp) != 8:
        print("process_read: Cannot read file", file=sys.stderr)
        return None

    tmp_id, tmp_size = struct.unpack('<4sI', tmp)

    # 読取結果からの条件分岐
    if tmp_id == b'fmt ':
        f.seek(-8, 1)
        tmp = f.read(24)
        if not tmp or len(tmp) != 24:
            print("process_read: Cannot read fmt chunk", file=sys.stderr)
            return None

        chunk_id, chunk_size, audio_format, channel_num, \
            sample_rate, byte_rate, block_align, bit_depth = struct.unpack('<4sIHHIIHH', tmp)

        if chunk_size > 16:                 # 取得したfmt のチャンクサイズと比較して、標準より大きかったら飛ばす
            f.seek(chunk_size - 16, 1)
        return {
            'chunk_id': chunk_id,
            'chunk_size': chunk_size,
            'audio_format': audio_format,
            'channel_num': channel_num,
            'sample_rate': sample_rate,
            'byte_rate': byte_rate,
            'block_align': block_align,
            'bit_depth': bit_depth
        }
    elif tmp_id == b'data':
        return {
            'chunk_id': tmp_id,
            'chunk_size': tmp_size
        }
    else:
        f.seek(tmp_size, 1)
        print(f"Unknown chunk is skipped", file=sys.stderr)
        return {
            'chunk_id': tmp_id
        }

def main():
    if len(sys.argv) != 2:
        print("Argument error", file=sys.stderr)
        return 1

    file_name = sys.argv[1]
    riff = None
    fmt = None
    data = None

    try:
        with open(file_name, "rb") as f:
            tmp = f.read(12)
            if not tmp or len(tmp) != 12:
                print("main: Cannot read file", file=sys.stderr)
                return 1

            tmp_id, tmp_size, tmp_format = struct.unpack('<4sI4s', tmp)
            if tmp_id == b'RIFF' and tmp_format == b'WAVE':
                riff = {
                    'chunk_id': tmp_id,
                    'chunk_size': tmp_size,
                    'format': tmp_format
                }
                print(f"Found RIFF header: {riff['chunk_id']}...{riff['format']}", file=sys.stderr)
            else:
                print("This file is not WAV", file=sys.stderr)
                return -1

            while fmt is None or data is None:
                tmp = process_read(f)

                if tmp is None:
                    print("process_read: returned error", file=sys.stderr)
                    return 1
                elif tmp['chunk_id'] == b'fmt ':
                    fmt = tmp
                elif tmp['chunk_id'] == b'data':
                    data = tmp

            if fmt is None or data is None:
                print("Cannot find fmt or data chunk", file=sys.stderr)
                return 1

        """
        === WAV File Information ===
        Audio format: 1 (PCM)
        Channels: 1 (Mono)
        Sample rate: 44100 Hz
        Bits per sample: 16
        Data size: 88200 bytes
        Duration: 1.00 seconds

        """
        title = ' WAV File Information '.center(30, '=')
        is_pcm = 'PCM' if fmt['audio_format'] == 1 else 'Unknown'
        is_mono = 'Mono' if fmt['channel_num'] == 1 else 'Stereo'
        bits_per_sample = fmt['bit_depth'] * fmt['channel_num']
        duration = data['chunk_size'] / (bits_per_sample / 8 * fmt['sample_rate'])

        print(title)
        print(f"Audio format: {fmt['audio_format']} ({is_pcm})")
        print(f"Channels: {fmt['channel_num']} ({is_mono})")
        print(f"Sample rate: {fmt['sample_rate']} Hz")
        print(f"Bits per sample: {bits_per_sample}")
        print(f"Data size: {data['chunk_size']} bytes")
        print(f"Duration: {duration:.2f}")
        print()

        return 0




    except FileNotFoundError as e:
        print(e)
        return 1
    except Exception as e:
        print(f"Exception/main: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
