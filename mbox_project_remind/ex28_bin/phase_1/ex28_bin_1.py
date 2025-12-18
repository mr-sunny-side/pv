import sys

"""
12-17: まずは2桁の16進数をhexdump標準出力形式で出力するコードを書いてみる
    - classオブジェクトにしようと思ったが、冗長すぎるのでやめた
"""

def print_bytes(bytes_line):
    if bytes_line:
        for bytes in bytes_line:
            print(f"{bytes:02x}", end=' ')

def print_ascii(bytes_line):
    if bytes_line:
        for bytes in bytes_line:
            print(f"{chr(bytes)}", end='') if 0x20 <= bytes <= 0x7f else print('.', end='')


def main():
    if len(sys.argv) != 3:
        print("Argument Error", file=sys.stderr)
        print("Usage: [This file] [BMP file] [How many line]")
        return 1

    file_name = sys.argv[1]
    line_num = int(sys.argv[2])
    offset = 0
    with open(file_name, 'rb') as f:
        # 16bytesごと読む、という作業を行うためのループ
        # なのでカウンタ変数は使わない(_)
        for _ in range(line_num):
            bytes_line = f.read(16)
            if not bytes_line:
                break

            print(f"{offset:08x}", end=' ')

            print_bytes(bytes_line)

            print('|', end='')
            print_ascii(bytes_line)
            print('|', end='\n')

            # オフセットアドレスは16進数
            # 一行16bytesなので、終わったら+16
            offset += 16

        return 0

if __name__ == '__main__':
    sys.exit(main())
