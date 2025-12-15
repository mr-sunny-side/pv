import sys


def split_line(model_line):
    if model_line:
        try:
            cpu_name = model_line.split(':')[1]
            return cpu_name if cpu_name else None
        except IndexError as e:
            print(e, file=sys.stderr)
            return None
        except Exception as e:
            print(e, file=sys.stderr)
            return None

with open('/proc/cpuinfo', 'r') as file:
    for line in file:
        line.strip()
        if line.startswith("model name"):
            result = split_line(line)
            print(result) if result else print(f"Cannot split {line}", file=sys.stderr)
            sys.exit(0)

    print("Cannot find 'model name'", file=sys.stderr)
    sys.exit(1)
