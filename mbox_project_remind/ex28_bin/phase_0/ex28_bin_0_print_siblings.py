import sys

def split_line(line):
    if line:
        try:
            info = line.split(':')[1].strip()
            return info if info else None
        except IndexError as e:
            print(e)
            return None

def main():
    cpu_name = None
    core_num = None
    logical_cores = None

    try:
        with open('/proc/cpuinfo', 'r') as file:
            for line in file:
                if line.startswith('model name'):
                    cpu_name = split_line(line)
                elif line.startswith('cpu cores'):
                    core_num = split_line(line)
                elif line.startswith('siblings'):
                    logical_cores = split_line(line)

                if cpu_name and core_num and logical_cores:
                    break


            if cpu_name and core_num and logical_cores:
                print(f"{'model name:':<25}{cpu_name}")
                print(f"{'cpu cores:':<25}{core_num}")
                print(f"{'siblings:':<25}{logical_cores}")
            else:
                print("Cannot find lines", file=sys.stderr)

    except FileNotFoundError as e:
        print(e)
        return 1
    except Exception as e:
        print(e)
        return 1

if __name__ == '__main__':
    sys.exit(main())
