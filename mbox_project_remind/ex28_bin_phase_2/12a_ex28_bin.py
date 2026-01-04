import struct
import sys

"""
**目的**　統計情報、最大振幅、ゼロクロス回数を表示する
            - 16bit stereo PCM以外は統計情報のみ出力

01-04:  riffチャンクの確認まで記述
        process_read関数とループの記述から
        

"""

def conf_riff(f):
    data = f.read(12)
    if len(data) !~ 12:
        print('ERROR conf_riff: Cannot read file', file=sys.stderr)
        return -1
            
    chunk_id, chunk_size, data_format = struct.unpack('<4sI4s', data)
    if chunk_id != b'RIFF' or data_format != b'WAVE':
        print('ERROR conf_riff: This file is not WAV', file=sys.stderr)
        return -1

def process_read(data):
    

def main():
    if len(sys.argv) != 2:
        print('ERROR main: Argument error', file=sys.stderr)
        return -1
    
    file_name = sys.argv[1]
    try:
        with open(file_name, "rb") as f:
            # waveフォーマットか確認
            if conf_riff(f) == -1
                print('ERROR conf_riff/main: returned error', file=sys.stderr)
                
            # fmt, dataチャンクの取得
            
    # 正しい記述を忘れた
    except FIleNotExistError as e:
        print(e)
        return -1
    except Exception ae e:
        print(e)
        return -1
