import sys

"""
12-17: まずは2桁の16進数をhexdump標準出力形式で出力するコードを書いてみる
    - こういうのでもクラス志向が可能なのか試す
    - 列アドレスごとに、02xデータとascii変換データを取り出せるようにする
    ⁻ 今回の場合、ストリーム処理の方がメモリ効率は圧倒的良い
"""

class HexDump:
    def __init__(self):
        pass


def main():
    if len(sys.argv) != 2:
        print("Argument Error", file=sys.stderr)
        print("Usage: [This file] [BMP file]")
        return 1

    file_name = sys.argv[1]
    with open(file_name, 'rb') as f:
        for bytes_line in f:
            bytes_line = f.read(16)
            if not bytes_line:
                break
