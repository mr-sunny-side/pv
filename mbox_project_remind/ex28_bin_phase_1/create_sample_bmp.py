#!/usr/bin/env python3
"""
8x8ピクセルのシンプルなBMPファイルを作成
グラデーションパターンを含む
"""

def create_sample_bmp():
    width = 8
    height = 8

    # BMPファイルヘッダー (14バイト)
    file_header = bytearray([
        0x42, 0x4D,              # 'BM' - BMPファイル識別子
        0x36, 0x01, 0x00, 0x00,  # ファイルサイズ (310バイト = 14 + 40 + 256)
        0x00, 0x00,              # 予約領域1
        0x00, 0x00,              # 予約領域2
        0x36, 0x00, 0x00, 0x00   # ピクセルデータへのオフセット (54バイト)
    ])

    # 情報ヘッダー (40バイト)
    info_header = bytearray([
        0x28, 0x00, 0x00, 0x00,  # ヘッダーサイズ (40バイト)
        0x08, 0x00, 0x00, 0x00,  # 画像の幅 (8ピクセル)
        0x08, 0x00, 0x00, 0x00,  # 画像の高さ (8ピクセル)
        0x01, 0x00,              # プレーン数 (常に1)
        0x18, 0x00,              # 1ピクセルあたりのビット数 (24ビット = RGB)
        0x00, 0x00, 0x00, 0x00,  # 圧縮方式 (0 = 無圧縮)
        0x00, 0x01, 0x00, 0x00,  # 画像データサイズ (256バイト)
        0x00, 0x00, 0x00, 0x00,  # 水平解像度
        0x00, 0x00, 0x00, 0x00,  # 垂直解像度
        0x00, 0x00, 0x00, 0x00,  # 使用色数
        0x00, 0x00, 0x00, 0x00   # 重要色数
    ])

    # ピクセルデータの作成（グラデーションパターン）
    pixel_data = bytearray()

    # BMPは下から上に向かって格納される
    for y in range(height - 1, -1, -1):
        for x in range(width):
            # グラデーションパターン: 左から右に明るくなる
            brightness = int(255 * x / (width - 1))
            # RGB値（BMPではBGRの順）
            blue = brightness
            green = brightness
            red = brightness
            pixel_data.extend([blue, green, red])

        # 各行は4バイトの倍数にパディングする必要がある
        # 8ピクセル * 3バイト = 24バイト → 既に4の倍数なのでパディング不要
        # しかし、例として計算方法を示す
        row_size = width * 3
        padding = (4 - (row_size % 4)) % 4
        pixel_data.extend([0x00] * padding)

    # ファイルに書き込み
    with open('sample.bmp', 'wb') as f:
        f.write(file_header)
        f.write(info_header)
        f.write(pixel_data)

    print("sample.bmp を作成しました")
    print(f"サイズ:{len(file_header) + len(info_header) + len(pixel_data)} バイト")
    print(f"画像サイズ:{width}x{height} ピクセル")

if __name__ == '__main__':
    create_sample_bmp()
