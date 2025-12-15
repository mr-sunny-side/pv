import sys

"""
/proc/cpuinfoから 'model name'と'cpu cores'行の内容を取り出す
"""

def split_line(line):
    if line:
        try:
            detail = line.split(':')[1].strip()
            return detail if detail else None
        except IndexError as e:
            print(e, file=sys.stderr)
            return None


def main():
    model_count = 0
    core_count = 0

    with open('/proc/cpuinfo', 'r') as file:
        for line in file:
            line = line.strip()
            if model_count == 1 and core_count == 1:
                return 0
            if line.startswith('model name'):
                model_count += 1
                cpu_name = split_line(line)
                print(cpu_name) if cpu_name else print(f"Cannot split {line}", file=sys.stderr)
            elif line.startswith('cpu cores'):
                core_count += 1
                core_number = split_line(line)
                print(core_number) if core_number else print(f"Cannot split {line}", file=sys.stderr)

        print("Cannot find line", sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
