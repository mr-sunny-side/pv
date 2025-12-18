import sys

"""
12-17: まずは2桁の16進数をhexdump標準出力形式で出力するコードを書いてみる
    - classオブジェクトにしようと思ったが、冗長すぎるのでやめた
"""

def print_byte(byte_line):
    if byte_line:
        for byte in byte_line:
            print(f"{byte:02x}", end=' ')

def print_ascii(byte_line):
    if byte_line:
        for byte in byte_line:
            print(f"{chr(byte)}", end='') if 0x20 <= byte <= 0x7f else print('.', end='')

# 型指定との衝突を避けるため、シンボルはbyteで統一
def main():
    if len(sys.argv) != 3:
        print("Argument Error", file=sys.stderr)
        print("Usage: [This file] [BMP file] [How many line]")
        return 1

    file_name = sys.argv[1]
    line_num = int(sys.argv[2])
    offset = 0
    with open(file_name, 'rb') as f:
        # 16byteごと読む、という作業を行うためのループ
        # なのでカウンタ変数は使わない(_)
        for _ in range(line_num):
            byte_line = f.read(16)
            if not byte_line:
                break

            print(f"{offset:08x}", end=' ')

            # 1列に16byteなかった際の処理
            if len(byte_line) < 16:
                print_byte(byte_line)
                for _ in range(16 - len(byte_line)):
                    print(' ', end=' ')

                print('|', end='')
                print_ascii(byte_line)
                for _ in range(16 - len(byte_line)):
                    print(' ', end='')
                print('|', end='\n')

            else:
                print_byte(byte_line)

                print('|', end='')
                print_ascii(byte_line)
                print('|', end='\n')

            # オフセットアドレスは16進数
            # 一行16byteなので、終わったら+16
            offset += 16

        return 0

if __name__ == '__main__':
    sys.exit(main())
