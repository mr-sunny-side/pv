import sys
import subprocess



def split_line(model_line):
    if model_line:
        try:
            cpu_name = model_line.split(':')[1].strip()
            return cpu_name if cpu_name else None
        except IndexError as e:
            print(e, file=sys.stderr)
            return None
        except Exception as e:
            print(e, file=sys.stderr)
            return None

def main():
    try:
        result = subprocess.run(
            ['cat', '/proc/cpuinfo'],
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        print(e, file=sys.stderr)
        return 1
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        return 1
    except Exception as e:
        print(e, file=sys.stderr)
        return 1

    cpu_info = result.stdout.strip().split('\n')

    for info in cpu_info:
        info = info.strip()
        if info.startswith('model name'):
            result = split_line(info)
            print(result) if result else print(f"Cannot split {info}", file=sys.stderr)
            return 0

    print("Cannot find 'model name'", file=sys.stderr)
    return 1

if __name__ == '__main__':
    sys.exit(main())
