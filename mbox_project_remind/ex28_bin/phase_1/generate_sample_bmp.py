# generate_sample_bmp.py
import struct

def create_simple_bmp(filename, width, height):
    """
    単純な赤色の画像を持つBMPファイルを生成する

    引数:
        filename: 出力ファイル名
        width: 画像の幅（ピクセル）
        height: 画像の高さ（ピクセル）
    """
    # BMPは4バイト境界にアラインする必要がある
    row_size = ((width * 3 + 3) // 4) * 4
    pixel_data_size = row_size * height
    file_size = 14 + 40 + pixel_data_size

    with open(filename, 'wb') as f:
        # ファイルヘッダー（14バイト）
        f.write(b'BM')  # ファイルタイプ（2バイト）
        f.write(struct.pack('<I', file_size))  # ファイルサイズ（4バイト）
        f.write(struct.pack('<H', 0))  # 予約領域1（2バイト）
        f.write(struct.pack('<H', 0))  # 予約領域2（2バイト）
        f.write(struct.pack('<I', 54))  # 画像データの開始位置（4バイト）

        # 情報ヘッダー（40バイト）
        f.write(struct.pack('<I', 40))  # ヘッダーサイズ
        f.write(struct.pack('<i', width))  # 画像の幅
        f.write(struct.pack('<i', height))  # 画像の高さ
        f.write(struct.pack('<H', 1))  # プレーン数
        f.write(struct.pack('<H', 24))  # ビット深度（24ビットカラー）
        f.write(struct.pack('<I', 0))  # 圧縮方式（0=無圧縮）
        f.write(struct.pack('<I', pixel_data_size))  # 画像データサイズ
        f.write(struct.pack('<i', 2835))  # 水平解像度（ピクセル/m）
        f.write(struct.pack('<i', 2835))  # 垂直解像度（ピクセル/m）
        f.write(struct.pack('<I', 0))  # 使用色数（0=全色）
        f.write(struct.pack('<I', 0))  # 重要色数（0=全色）

        # 画像データ（赤色の画像）
        for y in range(height):
            for x in range(width):
                f.write(bytes([0, 0, 255]))  # BGR形式（青、緑、赤）
            # 4バイト境界へのパディング
            padding = row_size - (width * 3)
            f.write(bytes([0] * padding))

if __name__ == '__main__':
    # 100x100ピクセルの赤い画像を生成
    create_simple_bmp('sample.bmp', 100, 100)
    print("sample.bmp を生成しました（100x100ピクセルの赤い画像）")
