# def	extract_domain(line):
# 	parts = line.split("@")
# 	return parts[1]

# partsの要素数でチェックする方法

# def	extract_domain(line):
# 	parts = line.split("@")
# 	if len(parts) >= 2:
# 		return parts[1]
# 	return None

# 許可より寛容を求める
# （EAFP: Easier to Ask for Forgiveness than Permission）
def	extract_domain(line):
	try:
		return line.split("@")[1]
	except IndexError:
		return None

test_cases = [
    'user@example.com',
    'admin@digitalgeek.tech',
    'notifications@github.com',
]

for line in test_cases:
	result = extract_domain(line)
	print(result)
