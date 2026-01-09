import subprocess
import ctypes
import sys
from email.header import decode_header

"""
1. まずsubprocessでext_senderのbytes列をキャッチし、構造を知る
2. それをdecodeして出力できるか確認

3. 試しに'@'で条件分岐してみる
    - エンコードされたものだけ綺麗に表示された。逆も然り

"""

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
            print(f"Decoding Error: {e}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"Decoding Error: {e}", file=sys.stderr)
            return None

def safe_ext_domain(lib, raw_email):
    if raw_email:
        """
        1. ext_domainの戻り値として抽出されたドメイン文字列のポインタを受け取る
        2. ctypes.string_at()でポインタ文字列として解釈し、bytes型に変換
        3. decode()してstr型に変換し、return

        """
        try:
            raw_domain_p = lib.ext_domain(raw_email)
            return ctypes.string_at(raw_domain_p).decode(), raw_domain_p
        except Exception as e:
            print(e)
            return None, None

def main():
    if len(sys.argv) != 4:
        print(f"[This.py] [ext_sender_file] [ext_domain.so] [.mbox]", file=sys.stderr)
        return 1

    ext_sender_file = sys.argv[1]
    ext_domain_so = sys.argv[2]
    mbox = sys.argv[3]

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
    except Exception as e:
        print(e)
        return 1

    sender_list = result.stdout.strip().split(b'\n')

    lib = ctypes.CDLL(ext_domain_so)

    """
    戻り値の文字列のポインタを保持し、後でfreeする必要がある
    そのため、ポインタを受け取るc_void_pでなければならない

    """

    lib.ext_domain.argtypes = [ctypes.c_char_p]
    lib.ext_domain.restype = ctypes.c_void_p
    # free_memoryも同様の理由でc_void_p
    lib.free_memory.argtypes = [ctypes.c_void_p]
    lib.free_memory.restype = None

    for raw_email in sender_list:

        """
        キャリッジターンが混入するので消す
        decode_headerをする際に、特殊文字の混入で文字化けが起こる

        """

        raw_email = raw_email.strip()
        if raw_email and b'@' not in raw_email:
            email = raw_email.decode()
            decode_sender = safe_decode(email)
            # このターンを終わらせるときは必ずcontinueを付ける
            if decode_sender:
                print(decode_sender)
                continue
            else:
                continue
        elif raw_email is None or raw_email == b'':
            continue

        # freeする対象であるdomainのポインタも受け取る
        domain, raw_domain_p = safe_ext_domain(lib, raw_email)
        email = raw_email.decode()
        if raw_domain_p and domain:
            print(f"{email:<50}->{domain:>40}")
            lib.free_memory(raw_domain_p)
        else:
            print(f"ext_domain Incomplete: {email},", file=sys.stderr)
            return 1


    return 0

if __name__ == '__main__':
    sys.exit(main())
