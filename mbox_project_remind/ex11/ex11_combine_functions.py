import re

def	extract_email(line):
	match = re.search(r'[\w\.-]+@[\w\.-]+', line)
	if match:
		return match.group()
	return None

def	extract_domain(line):
	try:
		return line.split("@")[1]
	except IndexError:
		return None

test_cases = [
    'From: user@example.com',
    'From: "John Doe" <john@digitalgeek.tech>',
]

for line in test_cases:
	email = extract_email(line)
	domain = extract_domain(line)
	print(domain)
