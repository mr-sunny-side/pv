#!/usr/bin/env python3
import sys
import struct

"""
    12-27: 関数内のfmt_countは記述として正しいか確認する

    fmt, dataを見つけて情報を出力する

    === Scanning chunks ===
    Found chunk: fmt  (size: 16 bytes)
    Found chunk: data (size: 88200 bytes)

    === WAV File Information ===
    Audio format: 1
    Channels: 1
    Sample rate: 44100 Hz
    Bits per sample: 16
    Data size: 88200 bytes
    Duration: 1.00 seconds

"""

def process_read(f):
    # 呼び出されたら、カレントポインタからchunk_idを読み取り、該当するチャンク情報を返す
    # 発見したチャンクのカウントはmainで行う （数値はイミュータブル・スコープの問題）

    tmp = f.read(12) if f else None

    if tmp is None or len(tmp) != 12:
        print("Error: Cannot read file", file=sys.stderr)
        return {
            'chunk_id': 'None'
        }

    tmp_id, tmp_size, tmp_format = struct.unpack('<4sI4s', tmp)

    if tmp_id == 'RIFF' and tmp_format == 'WAVE':   # チャンクが短いのでそのままreturn
        return {
            'chunk_id': tmp_id.decode('ascii'),
            'chunk_size': tmp_size,
            'format': tmp_format.decode('ascii')
        }
    elif tmp_id == 'fmt ':
        f.seek(-8, 1)    # チャンクの先頭に戻る

        fmt = f.read(24)

        if len(fmt) < 24:
            print("Error: Cannot read fmt chunk", file=sys.stderr)
            return {
                'chunk_id': 'None'
            }

        chunk_id, chunk_size, audio_format, channel_num, \
            sample_rate, bytes_rate, block_align, bit_depth = struct.unpack('<4sIHHIIHH', fmt)

        if chunk_size > 16:
            f.seek(chunk_size - 16, 1)  #16バイト以上のfmtチャンクの場合、残りを飛ばす

        return {
            'chunk_id': chunk_id.decode('ascii'),
            'chunk_size': chunk_size,
            'audio_format': audio_format,
            'channel_num': channel_num,
            'sample_rate':sample_rate,
            'bytes_rate': bytes_rate,
            'block_align': block_align,
            'bit_depth': bit_depth
        }

    elif tmp_id == 'data':  # チャンクが短いのでそのままreturn
        return {
            'chunk_id': tmp_id,
            'chunk_size': tmp_size
        }
    else:
        f.seek(tmp_size, 1)
        return {
            'chunk_id': 'None'
        }




def main():
    if len(sys.argv) != 2:
        print("Argument error", file=sys.stderr)
        return -1

    file_name = sys.argv[1]
    riff = None
    fmt = None
    data = None

    try:
        with open(file_name, "rb") as f:
            fmt_count = False
            data_count = False
            while (not fmt or not data or not riff):
                tmp = process_read(f)

                # tmp = Noneをprocess_readが返すとここでエラーが発生する
                # 教訓 - return Noneは予期しないエラーが発生する場合がある
                if tmp['chunk_id'] == "RIFF" and tmp['chunk_id'] == 'WAVE' and not riff:
                    riff = tmp
                elif tmp['chunk_id'] == "fmt " and not fmt:
                    fmt = tmp
                elif tmp['chunk_id'] == "data" and not data:
                    data = tmp

        if not riff or not fmt or not data:
            print("Error: Cannot find RIFF, fmt or data", file=sys.stderr)
            return 1

        """
        === Scanning chunks ===
        Found chunk: fmt  (size: 16 bytes)
        Found chunk: data (size: 88200 bytes)

        === WAV File Information ===
        Audio format: 1
        Channels: 1
        Sample rate: 44100 Hz
        Bits per sample: 16
        Data size: 88200 bytes
        Duration: 1.00 seconds

        """

        title = " Scanning Chunks ".center(25, '=')
        print(title)
        print(f"Found chunk: fmt  (size: {fmt['chunk_size']} bytes)")
        print(f"Found chunk: data (size: {data['chunk_size']} bytes)")
        print()

        title = " WAV File Information ".center(30, '=')
        is_pmc = "PMC" if fmt['audio_format'] == 1 else "Unknown"
        how_channel = "Mono" if fmt['channel_num'] == 1 else "Stereo"
        bits_per_sample = fmt['bit_depth'] * fmt['channel_num']
        duration =data['chunk_size'] / ((bits_per_sample / 8) * fmt['sample_rate'])

        print(title)
        print(f"Audio format: {fmt['audio_format']} ({is_pmc})")
        print(f"Channels: {fmt['channel_num']} ({how_channel})")
        print(f"Sample rate: {fmt['sample_rate']}")
        print(f"Bits per sample: {bits_per_sample}")
        print(f"Data size: {data['chunk_size']} bytes")
        print(f"Duration: {duration:.2f} seconds")

        return 0

    except FileNotFoundError as e:
        print(e)
        return 1
    except Exception as e:
        print(e)
        return 1

if __name__ == '__main__':
    sys.exit(main())
