import shutil
import sys

"""
    discのtotal,used,freeを、GB単位で出力する
    /proc/には該当の出力は無いので、pythonのshutilモジュールを利用
"""

def b_to_gb(df_str):
    if df_str:
        source_int = int(df_str)
        gb_int = source_int / (1024 ** 3) # 累乗の書き方
        return f"{gb_int:.1f} GB"


def main():

    # disk_usageはdfコマンドと違ってbytes単位で返す
    usage = shutil.disk_usage('/')

    disk_total = usage.total
    disk_used = usage.used
    disk_free = usage.free

    # マクロと表示用の関数を作ることで、毎回:<10と書かなくてよくなる
    print(f"{'total:':<10}{b_to_gb(disk_total):>10}")
    print(f"{'used:':<10}{b_to_gb(disk_used):>10}")
    print(f"{'free:':<10}{b_to_gb(disk_free):>10}")
    return 0

if __name__ == '__main__':
    sys.exit(main())
