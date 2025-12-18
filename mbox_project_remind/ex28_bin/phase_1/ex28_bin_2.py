import sys
import struct

L_WIDTH = 25
R_WIDTH = 25

"""
要件：
- `struct`モジュールを使用すること
- コマンドライン引数でファイル名を受け取ること
- ファイル識別子が"BM"でない場合はエラーメッセージを表示すること
- 各情報にラベルを付けて見やすく整形すること
- ファイルサイズはバイト単位に加えて、適切な単位(KB, MB)でも表示すること


期待される出力：

=== BMP Header Information ===
File Type: BM
File Size: 30054 bytes (29.3 KB)
Image Offset: 54 bytes
Image Width: 100 pixels
Image Height: 100 pixels
Bit Depth: 24 bits
Compression: None (0)

"""

def print_result(title, label, value):
    if title is not None:
        title = title.center(30, '=')
        print(title)
    print(f"{label + ':':<{L_WIDTH}}{value:>{R_WIDTH}}")





def main():
    if len(sys.argv) != 2:
        print("Argument Error", file=sys.stderr)
        print("Usage: [This file] [BMP file]", file=sys.stderr)
        return 1

    file_name = sys.argv[1]

    try:
        with open(file_name, 'rb') as f:
            f.seek(0) # ファイルのアドレスを指定のbyteに合わせる関数？
            file_header = f.read(14)

            # char*2, 符号なし4byte, 4byteスキップ、符号なし4byte
            signature, file_size, img_offset = struct.unpack('<2sIxxxxI', file_header)

            print(signature, file_size, img_offset, file=sys.stderr)

            if signature != b'BM':
                print('File is not BMP', file=sys.stderr)
                return 1

            # 画像サイズまで読む
            # 終端idx - 開始idx は距離が求められるという事を理解する
            f.seek(18)
            file_detail = f.read(8)
            img_width, img_hight = struct.unpack('<II', file_detail)

            print(img_width, img_hight, file=sys.stderr)

            # 圧縮情報まで読む
            f.seek(28)
            file_detail = f.read(6)
            bit_depth, compression = struct.unpack('<HI', file_detail)

            print(bit_depth, compression, file=sys.stderr)

            # 標準出力
            title = ' BMP Header Information '
            print_result(title, 'File Type' , str(signature))

            file_size_kb = f"{int(file_size) / 1024:.1f}"
            print_result(None, 'File Size', f"{str(file_size) + ' bytes (' + str(file_size_kb) + ' KB)'}")
            print_result(None, 'Imagine Offset', f"{str(img_offset) + ' bytes'}")
            print_result(None, 'Imagine Width', f"{str(img_width) + ' pixels'}")
            print_result(None, 'Imagine Width', f"{str(img_hight) + ' pixels'}")
            print_result(None, 'Bit Depth', f"{str(bit_depth) + ' bits'}")
            print_result(None, 'Compression', f"{str(compression)}")
            print()

            return 0

    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        return 1
    except Exception as e:
        print(e, file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
