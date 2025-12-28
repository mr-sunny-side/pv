#!/usr/bin/env python3
import sys
import struct

"""
    12-27: 関数内のfmt_countは記述として正しいか確認する
    12-28: sample2.wavでのエラー原因を特定する

            ```bash
            ./ex28_bin_9b.py $BIN_FILE/sample2.wav
                Error: Cannot read file
                process_read: returned None
            ```


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
    # 不明なチャンクの場合chunk_id = None, errorの場合Noneを返す

    tmp = f.read(8) if f else None

    if tmp is None or len(tmp) != 8:
        print("Error: Cannot read file", file=sys.stderr)
        return None

    tmp_id, tmp_size = struct.unpack('<4sI', tmp)

    # バイト型なのかstr型なのかを意識する
    if tmp_id == b'RIFF':   # チャンクが短いのでそのままreturn
        f.seek(-8, 1)
        tmp = f.read(12)
        if len(tmp) < 12:
            print("Cannot read RIFF header", file=sys.stderr)
            return None

        tmp_id, tmp_size, tmp_format = struct.unpack('<4sI4s', tmp)
        if tmp_format == b'WAVE':
            return {
                'chunk_id': tmp_id.decode('ascii'),
                'chunk_size': tmp_size,
                'format': tmp_format.decode('ascii')
            }
        else:
            print(f"This file is not WAV", file=sys.stderr)
            print(f"chunk_id: {tmp_id.decode()}")
            print(f"format: {tmp_format.decode()}")
            return None
    elif tmp_id == b'fmt ':
        f.seek(-8, 1)    # チャンクの先頭に戻る

        fmt = f.read(24)

        if len(fmt) < 24:
            print("Error: Cannot read fmt chunk", file=sys.stderr)
            return None

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

    elif tmp_id == b'data':  # チャンクが短いのでそのままreturn
        return {
            'chunk_id': tmp_id.decode('ascii'),
            'chunk_size': tmp_size
        }
    else:
        f.seek(tmp_size, 1)
        print(f"Unknown chunk is skipped: {tmp_id.decode()}", file=sys.stderr)
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
            i = 0
            while (not fmt or not data or not riff):
                tmp = process_read(f)
                i += 1


                # tmp = Noneをprocess_readが返すとここでエラーが発生する
                # 教訓 - return Noneは予期しないエラーが発生する場合がある
                if tmp and not riff and \
                    tmp['chunk_id'] == 'RIFF' and tmp['format'] == 'WAVE' :

                    riff = tmp
                elif tmp and not fmt and \
                    tmp['chunk_id'] == 'fmt ':

                    fmt = tmp
                elif tmp and not data and \
                        tmp['chunk_id'] == 'data' and not data:

                    data = tmp
                elif tmp and tmp['chunk_id'] == 'None':
                    continue
                elif tmp is None:
                    print("process_read: returned None")
                    print(f"i = {i}")

                    is_riff = True if riff else False
                    is_fmt = True if fmt else False
                    is_data = True if data else False

                    print(f"RIFF: {is_riff}")
                    print(f"fmt : {is_fmt}")
                    print(f"data: {is_data}")

                    return 1

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
