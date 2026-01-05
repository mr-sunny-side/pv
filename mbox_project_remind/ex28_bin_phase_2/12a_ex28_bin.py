#!/usr/bin/env python3

import struct
import sys

"""
**目的**　統計情報、最大振幅、ゼロクロス回数を表示する
            - 16bit stereo PCM以外は統計情報のみ出力

01-04:  fmt, dataチャンク取得、16bitPCM stereoの条件分岐まで記述
         - bin dataの取得ループから
"""

def process_read(f): # bool, fmt_chunk, data_size, data_offset
    data = f.read(8)
    if len(data) != 8:
        print('ERROR read/process_read: Cannot read file', file=sys.stderr)
        return False, None, None, None
    tmp_id, tmp_size = struct.unpack('<4sI', data)
    
    # fmt chunkの検証
    if tmp_id == b'fmt ':
        print('process_read: fmt chunk detected', file=sys.stderr)
        f.seek(-8, 1)   # fmt chunkの先頭へ移動
        
        # fmt chunkの読み込み
        data = f.read(24)
        if len(data) != 24:
            print('ERROR read/process_read: Cannot read fmt chunk', file=sys.stderr)
            return False, None, None, None
        
        chunk_id, chunk_size, audio_format, channel_num, \
            sample_rate, byte_rate, block_align, bit_depth = struct.unpack('<4sIHHIIHH', data)
            
        # fmt chunkが16byte以上の場合、スキップ
        if 16 < chunk_size:
            skip_size = chunk_size - 16
            f.seek(skip_size, 1)
            print('process_read: Rest of fmt chunk is skipped', file=sys.stderr)
    
        # fmt chunk辞書に書き込み
        print('process_read: fmt chunk is loaded', file=sys.stderr)
        fmt_chunk = {
            'chunk_id': chunk_id,
            'chunk_size': chunk_size,
            'audio_format': audio_format,
            'channel_num': channel_num,
            'sample_rate': sample_rate,
            'byte_rate': byte_rate,
            'block_align': block_align,
            'bit_depth': bit_depth
        }
        
        return True, fmt_chunk, None, None
    # data chunkの検証
    elif tmp_id == b'data':
        print('process_read: data chunk detected', file=sys.stderr)
        data_size = tmp_size
        data_offset = f.tell()
        print(f' - data_size: {data_size}', file=sys.stderr)
        print(f' - data_offset: {data_offset}', file=sys.stderr)
        # data chunkは必然的に最後のチャンクなので、終端までスキッ プの必要はない
        
        return True, None, data_size, data_offset
    else:
        f.seek(tmp_size, 1)
        print(f'process_read: Unknown chunk is skipped: [{tmp_id.decode()}]', file=sys.stderr)
        
        return True, None, None, None


def conf_riff(f):
    data = f.read(12)
    if len(data) != 12:
        print('ERROR conf_riff: Cannot read file', file=sys.stderr)
        return False
            
    chunk_id, chunk_size, data_format = struct.unpack('<4sI4s', data)
    
    if chunk_id != b'RIFF' or data_format != b'WAVE':
        print('ERROR conf_riff: This file is not WAV', file=sys.stderr)
        return False
        
    return True

def print_stat(fmt_chunk, data_size):
    """
    === WAV File Information ===
    Audio format: 1 (PCM)
    Channels: 1 (Mono)
    Sample rate: 44100 Hz
    Bits per sample: 16
    Data size: 88200 bytes
    Duration: 1.00 seconds
    
    """
    
    audio_format = fmt_chunk['audio_format']
    is_pcm = 'PCM' if audio_format == 1 else 'Unknown'
    
    channels = fmt_chunk['channel_num']
    is_mono = 'Mono' if channels == 1 else 'Stereo'
    
    sample_rate = fmt_chunk['sample_rate']
    bits_per_sample = fmt_chunk['bit_depth']
    duration = data_size / fmt_chunk['byte_rate']
    
    print('=== WAV File Information ===')
    print(f'Audio format: {audio_format} ({is_pcm})')
    print(f'Channels: {channels} ({is_mono})')
    print(f'Sample rate: {sample_rate} Hz')
    print(f'Bits per sample: {bits_per_sample}')
    print(f'Data size: {data_size}')
    print(f'Duration: {duration:.2f}')

def main():
    if len(sys.argv) != 2:
        print('ERROR main: Argument error', file=sys.stderr)
        return -1
    
    file_name = sys.argv[1]
    try:
        with open(file_name, "rb") as f:
            # waveフォーマットか確認
            if not conf_riff(f):
                print('ERROR conf_riff/main: returned error', file=sys.stderr)
                return -1
                
            # fmt, dataチャンクの取得
            process_bool = False
            fmt_chunk = None
            data_size = None
            data_offset = None
            while not fmt_chunk or not data_size or not data_offset:
                # process_readがエラーを返したら、一旦ループをやめる
                process_bool, tmp_fmt, tmp_size, tmp_offset = \
                    process_read(f)
                if process_bool == False:
                    break
                if tmp_fmt:
                    fmt_chunk = tmp_fmt
                elif tmp_size and tmp_offset:   # data_size, data_offsetは同時に見つかる
                    data_size = tmp_size
                    data_offset = tmp_offset
            
            # 各チャンクが読み込まれているか検証
            if not fmt_chunk or not data_size or not data_offset:
                print('ERROR main: Cannot find fmt or data chunk', file=sys.stderr)
                return -1
            
            #16bitPCM stereoか検証
            #違ったら統計情報をそのまま出力
            if fmt_chunk['audio_format'] != 1 or fmt_chunk['bit_depth'] != 16 or \
                fmt_chunk['channel_num'] != 2:
                print('main: This file is not 16bitPCM Stereo WAV', file =sys.stderr)
                print('', file=sys.stderr)
                print_stat(fmt_chunk, data_size)    # 統計情報をprint
                
                return 0
                
            # 最大振幅、ゼロクロスの走査
            f.seek(data_offset)     # data_offsetへ移動
            
            byte_depth = fmt_chunk['bit_depth'] / 8     # byte単位に変換
            while True:     # bin data取得ループ
                sample_l = f.read(byte_depth)
                sample_r = f.read(byte_depth)
                
                if sample_l == b'' and sanple_r == b'':     # eofを検出
                    break
                elif len(sample_l) != byte_depth of len(sample_r) != byte_depth:
                    print('ERROR read/main: Cannot read bin data', file=sys.stderr) # errorを別に検出
                    return -1
                    
                
                
            return 0
                
                
            
    except FileNotFoundError as e:
        print(e)
        return -1
    except Exception as e:
        print(e)
        return -1
        
if __name__ == '__main__':
    sys.exit(main())
    
    
"""
"""
