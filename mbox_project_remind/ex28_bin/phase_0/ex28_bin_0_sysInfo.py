import sys
import shutil

L_WIDTH = 50
R_WIDTH = 50

"""
    12-16: 次から積極的にクラスを利用する事

    /cpuinfo
        - model name
        - cpu cores
        - siblings

    /meminfo
        - MemTotal
        - MemAvailable
        - kB表示なので、GB:.1fに統一する

    shutil
        - total
        - used
        - free
        - bytes表示なので、上に同じ

    ! point !
        - /proc/は仮想ファイルなので、繰り返し開くのは基本的に問題ない
        - 表示フォーマット用の関数を作ってみる
"""

def split_line(line):
    if line:
        try:
            info = line.split(':')[1].strip()
            return info if info else None
        except IndexError:
            return "Cannot split"

def bytes_to_gb(bytes_str):
    if bytes_str:
        bytes_int = int(bytes_str)
        gb_int = bytes_int / (1024 ** 3)
        return gb_int
    else:
        return "bytes_to_gb: Argument is None"

def kb_to_gb(kb_str):
    if kb_str:
        kb_int = int(kb_str)
        gb_int = kb_int / (1024 ** 2)
        return gb_int
    else:
        return "kb_to_gb: Argument is None"


def conf_cpuInfo():
    # ネストが深すぎるのでtry文は省略
    c_name = None
    core_n = None
    sibs = None

    with open('/proc/cpuinfo', 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('model name'):
                c_name = line
            elif line.startswith('cpu cores'):
                core_n = line
            elif line.startswith('siblings'):
                sibs = line

            if c_name and core_n and sibs:
                break

        if c_name and core_n and sibs:
            return c_name, core_n, sibs
        else:
            return None, None, None

def conf_memInfo():
    # ネストが深すぎるのでtry文は省略
    mem_ttl = None
    mem_avai = None

    with open('/proc/meminfo', 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('MemTotal'):
                mem_ttl = line
            elif line.startswith('MemAvailable'):
                mem_avai = line

            if mem_ttl and mem_avai:
                break

        if mem_ttl and mem_avai:
            return mem_ttl, mem_avai
        else:
            return None, None

def conf_df():
    usage = shutil.disk_usage('/')

    d_total = usage.total
    d_used = usage.used
    d_free = usage.free

    return d_total, d_used, d_free

def print_format(title, label, value):
    if title:
        title = f"{title.center(100, "=")}"
        print(title)
    if isinstance(value, (int, float)): # str -> int -> / 1024でfloatになってるので条件はfloatと保険でint
        # GBが飛び出すが、f-stringのネストは面倒すぎるので無視
        print(f"{label + ':':<{L_WIDTH}}{value:>{R_WIDTH}.1f} GB") # フォーマット指定の順序: {値:埋め文字 寄せ方向 幅.精度 型}
    else:
        print(f"{label + ':':<{L_WIDTH}}{value:>{R_WIDTH}}")

def main():
    cpu_name = None
    core_num = None
    siblings = None

    mem_total = None
    mem_able = None

    disk_total = None
    disk_used = None
    disk_free = None

    try:
        # 未初期化のエラーが出たので、全部初期化した
            # 多分、書く関数のline.strip()を
            # 再代入していなかったのが原因だと後で気付いた

        # 辞書で記録すれば冗長なコードを改善できたかもしれない
        cpu_name, core_num, siblings = conf_cpuInfo()
        mem_total, mem_able = conf_memInfo()
        disk_total, disk_used, disk_free = conf_df()

        cpu_name = split_line(cpu_name)
        core_num = split_line(core_num)
        siblings = split_line(siblings)
        # MemInfoは二回splitする必要がある
        mem_total = split_line(mem_total).split()[0].strip()
        mem_able = split_line(mem_able).split()[0].strip()

        mem_total = kb_to_gb(mem_total)
        mem_able = kb_to_gb(mem_able)

        disk_total = bytes_to_gb(disk_total)
        disk_used = bytes_to_gb(disk_used)
        disk_free = bytes_to_gb(disk_free)

        if cpu_name and core_num and siblings:
            print_format('CPU Info', 'model name', cpu_name)
            print_format(None, 'cpu cores', core_num)
            print_format(None, 'siblings' ,siblings)
            print()
        else:
            print("CPU Info is incomplete", file=sys.stderr)

        if mem_total and mem_able:
            print_format('Memory Info', 'MemTotal', mem_total)
            print_format(None, 'MemAvailable', mem_able)
            print()
        else:
            print("Memory Info is incomplete", file=sys.stderr)

        if disk_total and disk_used and disk_free:
            print_format('Disk Free', 'total', disk_total)
            print_format(None, 'used', disk_used)
            print_format(None, 'free', disk_free)
            print()
        else:
            print("Disk Free Info is Incomplete", file=sys.stderr)
        return 0
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        return 1
    except IndexError as e:
        print(e, file=sys.stderr)
        return 1
    except Exception as e:
        print(e, file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
