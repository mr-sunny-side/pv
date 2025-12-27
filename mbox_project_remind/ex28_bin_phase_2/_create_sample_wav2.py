#!/usr/bin/env python3
"""
複雑なチャンク構造を持つWAVファイルを作成
- 未知のチャンク(JUNK, LISTなど)を含む
- チャンクの順序が標準的でない
- 拡張fmtチャンク(18バイト版)のオプション
- プログラムのロバスト性をテストするための「意地悪な」WAVファイル
"""
import struct
import math

def create_complex_wav(output_file='sample2.wav', use_extended_fmt=False):
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
        t = i / sample_rate
        value = amplitude * math.sin(2 * math.pi * frequency * t)
        sample = int(value * 32767)
        samples.append(sample)

    # サンプルデータをバイト列に変換
    sample_data = bytearray()
    for sample in samples:
        sample_data.extend(struct.pack('<h', sample))

    data_size = len(sample_data)

    # === 各チャンクの作成 ===

    # 1. fmtチャンク（標準16バイト or 拡張18バイト）
    fmt_chunk = bytearray()
    fmt_chunk.extend(b'fmt ')

    if use_extended_fmt:
        # 拡張フォーマット（cbSize=0を追加）
        fmt_chunk.extend(struct.pack('<I', 18))        # チャンクサイズ = 18
        fmt_chunk.extend(struct.pack('<H', 1))         # オーディオフォーマット（1=PCM）
        fmt_chunk.extend(struct.pack('<H', 1))         # チャンネル数
        fmt_chunk.extend(struct.pack('<I', sample_rate))
        fmt_chunk.extend(struct.pack('<I', sample_rate * 2))
        fmt_chunk.extend(struct.pack('<H', 2))         # ブロックアライン
        fmt_chunk.extend(struct.pack('<H', 16))        # ビット深度
        fmt_chunk.extend(struct.pack('<H', 0))         # cbSize = 0（拡張データなし）
        fmt_size = 26  # 8 (header) + 18 (data)
    else:
        # 標準フォーマット
        fmt_chunk.extend(struct.pack('<I', 16))
        fmt_chunk.extend(struct.pack('<H', 1))
        fmt_chunk.extend(struct.pack('<H', 1))
        fmt_chunk.extend(struct.pack('<I', sample_rate))
        fmt_chunk.extend(struct.pack('<I', sample_rate * 2))
        fmt_chunk.extend(struct.pack('<H', 2))
        fmt_chunk.extend(struct.pack('<H', 16))
        fmt_size = 24  # 8 (header) + 16 (data)

    # 2. JUNKチャンク（パディング用の無視すべきチャンク）
    junk_chunk = bytearray()
    junk_chunk.extend(b'JUNK')
    junk_data = b'This is padding data to test chunk skipping!\x00' * 3
    junk_chunk.extend(struct.pack('<I', len(junk_data)))
    junk_chunk.extend(junk_data)
    junk_size = 8 + len(junk_data)

    # 3. LISTチャンク（メタデータ用、通常は無視される）
    list_chunk = bytearray()
    list_chunk.extend(b'LIST')
    # LISTチャンクの中身（INFO/ISFTタグ）
    list_data = bytearray()
    list_data.extend(b'INFO')  # LIST type
    list_data.extend(b'ISFT')  # Software tag
    software_name = b'Python WAV Generator\x00'
    list_data.extend(struct.pack('<I', len(software_name)))
    list_data.extend(software_name)

    list_chunk.extend(struct.pack('<I', len(list_data)))
    list_chunk.extend(list_data)
    list_size = 8 + len(list_data)

    # 4. dataチャンク
    data_chunk = bytearray()
    data_chunk.extend(b'data')
    data_chunk.extend(struct.pack('<I', data_size))
    data_chunk.extend(sample_data)
    data_chunk_size = 8 + data_size

    # RIFFヘッダー
    # ファイルサイズ = fmt + JUNK + LIST + data
    file_data_size = fmt_size + junk_size + list_size + data_chunk_size

    riff_chunk = bytearray()
    riff_chunk.extend(b'RIFF')
    riff_chunk.extend(struct.pack('<I', 4 + file_data_size))  # "WAVE" + すべてのチャンク
    riff_chunk.extend(b'WAVE')

    # ファイルに書き込み（意地悪な順序: fmt → JUNK → LIST → data）
    with open(output_file, 'wb') as f:
        f.write(riff_chunk)
        f.write(fmt_chunk)
        f.write(junk_chunk)    # 未知のチャンク1
        f.write(list_chunk)    # 未知のチャンク2
        f.write(data_chunk)

    total_size = 12 + file_data_size

    print(f"{output_file} を作成しました")
    print(f"\n=== ファイル構造 ===")
    print(f"1. RIFF header: 12 bytes")
    print(f"2. fmt  chunk:  {fmt_size} bytes {'(Extended format with cbSize)' if use_extended_fmt else '(Standard PCM format)'}")
    print(f"3. JUNK chunk:  {junk_size} bytes (Should be skipped)")
    print(f"4. LIST chunk:  {list_size} bytes (Should be skipped)")
    print(f"5. data chunk:  {data_chunk_size} bytes")
    print(f"\n=== オーディオ情報 ===")
    print(f"サンプリングレート: {sample_rate} Hz")
    print(f"チャンネル数: 1 (Mono)")
    print(f"ビット深度: 16 bits")
    print(f"長さ: {duration} 秒")
    print(f"周波数: {frequency} Hz")
    print(f"\n=== ファイルサイズ ===")
    print(f"合計: {total_size} bytes")
    print(f"\nこのファイルは以下の点でテストに適しています:")
    print("- fmt チャンクの後に未知のチャンク(JUNK, LIST)が存在")
    print("- data チャンクが最後に配置されている")
    print("- プログラムは未知のチャンクを正しくスキップする必要がある")
    if use_extended_fmt:
        print("- 拡張fmt形式(18バイト)を使用")

def main():
    import sys

    print("=== 複雑なWAVファイル生成ツール ===\n")

    # オプション1: 標準フォーマット（複雑なチャンク構造）
    print("[1] 標準fmt形式の複雑なWAVファイルを作成中...")
    create_complex_wav('sample2.wav', use_extended_fmt=False)

    print("\n" + "="*60 + "\n")

    # オプション2: 拡張フォーマット（さらに複雑）
    print("[2] 拡張fmt形式の複雑なWAVファイルを作成中...")
    create_complex_wav('sample2_extended.wav', use_extended_fmt=True)

    print("\n" + "="*60)
    print("\n作成完了！")
    print("- sample2.wav: 標準fmt(16バイト) + 未知チャンク")
    print("- sample2_extended.wav: 拡張fmt(18バイト) + 未知チャンク")

if __name__ == '__main__':
    main()
