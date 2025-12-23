#!/usr/bin/env python3
"""
1秒間の440Hz（ラの音）サイン波を含むWAVファイルを作成
モノラル、16ビット、44.1kHzサンプリングレート
"""
import struct
import math

def create_sample_wav():
    # パラメータ
    sample_rate = 44100      # サンプリングレート（Hz）
    duration = 1.0           # 長さ（秒）
    frequency = 440.0        # 周波数（Hz）- ラの音
    amplitude = 0.5          # 振幅（0.0〜1.0）

    # サンプル数を計算
    num_samples = int(sample_rate * duration)

    # サイン波を生成
    samples = []
    for i in range(num_samples):
        # 時刻（秒）
        t = i / sample_rate
        # サイン波の値（-1.0 〜 1.0）
        value = amplitude * math.sin(2 * math.pi * frequency * t)
        # 16ビット整数に変換（-32768 〜 32767）
        sample = int(value * 32767)
        samples.append(sample)

    # サンプルデータをバイト列に変換
    sample_data = bytearray()
    for sample in samples:
        # 16ビット符号付き整数をリトルエンディアンで格納
        sample_data.extend(struct.pack('<h', sample))

    # データサイズ
    data_size = len(sample_data)

    # RIFFチャンクヘッダー (12バイト)
    riff_chunk = bytearray()
    riff_chunk.extend(b'RIFF')                           # チャンクID
    riff_chunk.extend(struct.pack('<I', 36 + data_size)) # チャンクサイズ
    riff_chunk.extend(b'WAVE')                           # フォーマット

    # fmtチャンク (24バイト)
    fmt_chunk = bytearray()
    fmt_chunk.extend(b'fmt ')                      # チャンクID
    fmt_chunk.extend(struct.pack('<I', 16))        # チャンクサイズ
    fmt_chunk.extend(struct.pack('<H', 1))         # オーディオフォーマット（1=PCM）
    fmt_chunk.extend(struct.pack('<H', 1))         # チャンネル数（1=モノラル）
    fmt_chunk.extend(struct.pack('<I', sample_rate)) # サンプリングレート
    fmt_chunk.extend(struct.pack('<I', sample_rate * 2)) # バイトレート
    fmt_chunk.extend(struct.pack('<H', 2))         # ブロックアラインメント
    fmt_chunk.extend(struct.pack('<H', 16))        # ビット深度

    # dataチャンク (8バイト + データ)
    data_chunk = bytearray()
    data_chunk.extend(b'data')                     # チャンクID
    data_chunk.extend(struct.pack('<I', data_size)) # チャンクサイズ
    data_chunk.extend(sample_data)                 # サンプルデータ

    # ファイルに書き込み
    with open('sample.wav', 'wb') as f:
        f.write(riff_chunk)
        f.write(fmt_chunk)
        f.write(data_chunk)

    print("sample.wav を作成しました")
    print(f"サンプリングレート:{sample_rate} Hz")
    print(f"長さ:{duration} 秒")
    print(f"周波数:{frequency} Hz")
    print(f"サンプル数:{num_samples}")
    print(f"ファイルサイズ:{12 + 24 + 8 + data_size} バイト")

if __name__ == '__main__':
    create_sample_wav()
