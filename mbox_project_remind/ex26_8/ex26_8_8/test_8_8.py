import subprocess
import sys
from email.header import decode_header

"""
1. まずsubprocessでext_senderのbytes列をキャッチし、構造を知る
2. それをdecodeして出力できるか確認

3. 試しに'@'で条件分岐してみる
    - エンコードされたものだけ綺麗に表示された。逆も然り

"""

def main():
    if len(sys.argv) != 3:
        print(f"[{sys.argv[0]}] [ext_sender] [.mbox]", file=sys.stderr)
        return 1

    ext_sender_file = sys.argv[1]
    mbox = sys.argv[2]

    try:
        result = subprocess.run(
            [ext_sender_file, mbox],
            capture_output=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(e)
        return 1
    except FileNotFoundError as e:
        print(e)
        return 1

    sender_list = result.stdout.strip().split(b'\n')


    for email in sender_list:
        if b'@' in email:
            print(email.decode())

    return 0

if __name__ == '__main__':
    sys.exit(main())
