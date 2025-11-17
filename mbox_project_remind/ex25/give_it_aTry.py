import sys

if len(sys.argv) != 2:
    print("使い方: python3 inspect_mbox.py <mboxファイル>")
    sys.exit(1)

file_name = sys.argv[1]
line_count = 0
mail_count = 0
max_lines = 100  # 最初の100行だけを見る

print("=== mboxファイルの構造確認 ===\n")

with open(file_name, "r", encoding="utf-8", errors="ignore") as file:
    for line in file:
        line_count += 1
        if line.startswith("From "):
            mail_count += 1
            print(f"\n--- メール #{mail_count} 開始 (行番号: {line_count}) ---")

        print(f"{line_count}: {line.rstrip()}")

        if line_count >= max_lines:
            break

print(f"\n=== 最初の{line_count}行の中に{mail_count}通のメールがありました ===")
