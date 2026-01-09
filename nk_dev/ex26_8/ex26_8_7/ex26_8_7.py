import sys
import subprocess
from email.header import decode_header

def ext_domain(email):
    if email:
        try:
            domain = email.split('@')[1]
            return domain
        except IndexError as e:
            print(f"Index Error: {e}", file=sys.stderr)
            print(f"Trying Email: {email}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"Unexpected Error: {e}", file=sys.stderr)
            print(f"Trying Email: {email}", file=sys.stderr)
            return None

def decode_email(email):
    if email:
        parts = []
        try:
            unpacked = decode_header(email)
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
            print(f"Type Error when Decoding: {e}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"Unexpected Error when Decoding: {e}", file=sys.stderr)
            return None



def main():
    if len(sys.argv) < 2:
        print("Argument Error", file=sys.stderr)
        print(f"[{sys.argv[0]}] [Extract .c program] [.mbox file]", file=sys.stderr)
        return 1
    elif sys.argv[1] == "-h" or sys.argv[1] == "--help":
        print(f"[{sys.argv[0]}] [Extract .c program] [.mbox file]", file=sys.stderr)
        return 0
    elif len(sys.argv) == 3:
        c_file = sys.argv[1]
        mbox_file = sys.argv[2]

        try:
            result = subprocess.run(
                [c_file, mbox_file],
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"Error Detected: {e}", file=sys.stderr)
            return 1
        except FileNotFoundError as e:
            print(f"Cannot Open File: {e}", file=sys.stderr)
            return 1

        emails = result.stdout.strip().split('\n')

        domain_dict = {}
        for email in emails:
            if email and '@' in email:
                domain = ext_domain(email)
            elif email and '@' not in email:
                result = decode_email(email)

            if domain:
                domain_dict[domain] = domain_dict.get(domain, 0) + 1
            elif result:
                domain_dict[result] = domain_dict.get(result, 0) + 1

            domain, result = None, None

        sorted_list = sorted(
            domain_dict.items(),
            key=lambda x: x[1],
            reverse=True
            )

        title = 'Top 5 Domains'.center(100, '=')
        print(f"{title}\n")
        for domain, count in sorted_list[:5]:
            print(f"{domain:<50}{count:>50}")

        title_sec = 'All Domains'.center(100, '=')
        print()
        print(f"{title_sec}\n")
        for domain, count in sorted_list:
            print(f"{domain:<50}{count:>50}")
        print()

        return 0

if __name__ == '__main__':
    sys.exit(main())
