import sys
import re
import time

"""
今回の目的は.cとcpc時間を比較する事
その為デコードは行わず、純粋にFrom: からemailを取り出す処理を行う

12-10:
    1. このコードのレビュー
    2. テスト実行によるCPU時間比較のためのShellScript作成
"""


def print_help(prog_name):
    print("=== How to Use ===", file=sys.stderr)
    print(f"[{prog_name}] [.mbox file]", file=sys.stderr)
    print("", file=sys.stderr)
    print("This program extract sender emails from an mbox file", file=sys.stderr)
    print("Command '-h' or '--help' to show this message", file=sys.stderr)

def print_status(line_num, cpu_time):
    print("=== Statistics ===", file=sys.stderr)
    print("", file=sys.stderr)
    print(f"Total Lines: {line_num}", file=sys.stderr)
    print(f"Processing Time: {cpu_time:.3f} s", file=sys.stderr)

def ext_sender(from_line):
    if from_line:
        # []の中では、'.'は特殊文字ではないので、\は不要
        email = re.search(r"[\w.-]+@[\w.-]+", from_line)
        return email.group() if email else None

def main():
    if len(sys.argv) != 2:
        print("Argument Error", file=sys.stderr)
        return 1
    if "-h" == sys.argv[1] or "--help" == sys.argv[1]:
        print_help(sys.argv[0])
        return 0

    file_name = sys.argv[1]
    line_num = 0
    # pythonでcpu時間を出すときの関数
    start_clock = time.process_time()

    try:
        with open(file_name, "r") as file:
            for line in file:
                line_num += 1
                # startswithは正規表現を使わない
                # 先頭文字列を確認するだけ
                if line.startswith("From: "):
                    email = ext_sender(line)
                    print(f"{line_num}: {email}") if email else print(f"{line_num}: Extract Failed")
    except FileNotFoundError:
        print(f"Error: Cannot Open {file_name}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected Error Detected: {e}", file=sys.stderr)
        return 1

    end_clock = time.process_time()
    cpu_time = end_clock - start_clock
    print_status(line_num, cpu_time)
    return 0


"""
このソースコードが直接実行された場合、mainの戻り値をプログラムが返す
.cのmain関数的な実装をする際の記述
もっとも、.pyでは必ずしも必要ではないので、明確な意図があることが多い。詳しくはNotionを参照
"""

if __name__ == '__main__':
    sys.exit(main())
