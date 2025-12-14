#!/usr/bin/env python3
import subprocess
import sys

if len(sys.argv) != 3:
    print("Usage: python3 debug_sender_list.py <ext_sender_file> <mbox>")
    sys.exit(1)

ext_sender_file = sys.argv[1]
mbox = sys.argv[2]

result = subprocess.run(
    [ext_sender_file, mbox],
    capture_output=True,
    check=True
)

sender_list = result.stdout.strip().split(b'\n')

print(f"Total entries: {len(sender_list)}\n")

# 最初の20エントリを詳細表示
print("=== First 20 entries ===")
for i, raw_email in enumerate(sender_list[:20]):
    has_at = b'@' in raw_email
    repr_str = repr(raw_email)
    decoded = raw_email.decode('utf-8', errors='replace')

    print(f"[{i:3d}] has_@: {has_at}")
    print(f"      repr : {repr_str}")
    print(f"      text : {decoded}")
    print()

# "freee" を含むエントリを検索
print("\n=== Entries containing 'freee' ===")
for i, raw_email in enumerate(sender_list):
    if b'freee' in raw_email.lower():
        print(f"[{i:3d}] has_@: {b'@' in raw_email}")
        print(f"      repr : {repr(raw_email)}")
        print(f"      text : {raw_email.decode('utf-8', errors='replace')}")
        print()

# エンコードされた文字列を含むエントリをいくつか表示
print("\n=== Entries with encoded strings (=?...?=) ===")
count = 0
for i, raw_email in enumerate(sender_list):
    if b'=?' in raw_email and b'?=' in raw_email:
        print(f"[{i:3d}] has_@: {b'@' in raw_email}")
        print(f"      repr : {repr(raw_email)}")
        print(f"      text : {raw_email.decode('utf-8', errors='replace')}")
        print()
        count += 1
        if count >= 10:
            break
