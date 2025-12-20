import sys

def split_line(line):
    if line:
        try:
            info = line.split(':')[1].strip()
            return info if info else None
        except IndexError:
            return "Cannot split"

def format_mem(mem_str):
    if mem_str:
        kb_str = mem_str.split()[0].strip()
        kb_int = int(kb_str)
        gb_int = kb_int / 1024 / 1024
        return f"{gb_int:.1f} GB"

def main():
    mem_able = None
    mem_total = None

    try:
        with open('/proc/meminfo', 'r') as file:
            for line in file:
                line = line.strip()
                if line.startswith('MemTotal'):
                    mem_total = split_line(line)
                    mem_total = format_mem(mem_total)
                elif line.startswith('MemAvailable'):
                    mem_able = split_line(line)
                    mem_able = format_mem(mem_able)

                if mem_able and mem_total:
                    break

            if mem_able and mem_total:
                print(f"{'MemTotal':<25}{mem_total}")
                print(f"{'MemAvailable:':<25}{mem_able}")
                return 0
            else:
                print(f"Cannot find lines", file=sys.stderr)
                return 1
    except FileNotFoundError as e:
        print(e)
        return 1
    except Exception as e:
        print(e)
        return 1

if __name__ == '__main__':
    sys.exit(main())
