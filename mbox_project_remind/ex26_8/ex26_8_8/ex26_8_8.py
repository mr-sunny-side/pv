import ctypes
import subprocess
import sys
from email.header import decode_header

def safe_decode(raw_line):
    if raw_line:
        parts = []
        try:
            unpacked = decode_header(raw_line)
            for data, encoding in unpacked:
                if isinstance(data, bytes):
                    decoded = data.decode(encoding or 'utf-8')
                else:
                    decoded = data
                parts.append(decoded)

            result = ''.join(parts)
            return result
        except UnicodeDecodeError as e:
            print(f"Decoding Error: {e}", file=sys.stderr)
            return None
        except TypeError as e:
            print(f"Decoding Type Error: {e}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"Unexpected Decoding Error: {e}", file=sys.stderr)
            return None



def main():
    if len(sys.argv) < 2:
        print("Argument Error", file=sys.stderr)
        print(f"Usage: [{sys.argv[0]}] [ext_sender .c file] [ext_domain lib file] [.mbox file]", file=sys.stderr)
        return 1
    elif sys.argv[1] == '-h' or sys.argv[1] == '--help':
        print(f"Usage: [{sys.argv[0]}] [ext_sender .c file] [ext_domain lib file] [.mbox file]", file=sys.stderr)
        return 0
    elif len(sys.argv) == 4:
        ext_sender_file = sys.argv[1]
        ext_domain_file = sys.argv[2]
        mbox = sys.argv[3]

        try:
            result = subprocess.run(
                [ext_sender_file, mbox],
                capture_output=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"ext_sender .c prog Error: {e}", file=sys.stderr)
            return 1
        except FileNotFoundError as e:
            print(f"Cannot Open File: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Unexpected Error in subprocess: {e}", file=sys.stderr)
            return 1

        # 今回はbytes型でもらうので、bを記述
        email_list = result.stdout.strip().split(b'\n')

        # .cを明確に示し、共有ライブラリを開く
        lib = ctypes.CDLL(ext_domain_file)

        # 共有ライブラリのext_domainの戻り値・引数型を定義
        lib.ext_domain.argtypes = [ctypes.c_char_p]
        lib.ext_domain.restype = ctypes.c_char_p
        lib.free_memory.argtypes = [ctypes.c_char_p]
        lib.free_memory.restype = None

        for email in email_list:
            if b'@' in email:
                domain = lib.ext_domain(email)
                print(f"{email.decode():<45} -> {domain.decode():>50}") if domain else None
                lib.free_memory(domain)
            else:
                decoded_email = safe_decode(email.decode())
                print(decoded_email)

        return 0

if __name__ == '__main__':
    sys.exit(main())
