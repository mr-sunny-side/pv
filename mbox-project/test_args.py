import sys

print(f"引数の数: {len(sys.argv)}")
print(f"引数一覧: {sys.argv}")

if len(sys.argv) >= 2:
	print(f"最初の引数: {sys.argv[1]}")
