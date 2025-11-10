import re

test_cases = [
    'From: user@example.com',
    'From: "John Doe" <john@example.com>',
    'From: notifications@github.com',
]

def	extract_email(line):
	match = re.search(r'[\w\.-]+@[\w\.-]+', line)
	if match:
		return match.group()
	return None

for line in test_cases:
	result = extract_email(line)
	print(result)



# test = 'From: "John Doe" <john@example.com>'
# result = extract_email(test)
# print(result)

# groupの使い方練習

# text = "From: admin@digitalgeek.tech"

# match1 = re.search(r'[\w\.-]+@[\w\.-]+', text)
# print(match1.group())

# match2 = re.search(r'([\w\.-]+)@([\w\.-]+)', text)
# print(match2.group())
# print(match2.group(1))
# print(match2.group(2))
