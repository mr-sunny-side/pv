import re

emails = []

def	extract_sender(line):
	if line.startswith("From: "):
		return line
	return None

def	extract_email(line):
	if line:
		match = re.search(r"[\w\.-]+@[\w\.-]+", line)
		if match:
			return match.group()
		return None

with	open("sample.mbox", "r") as file:
	for line in file:
		line = line.rstrip()
		sender = extract_sender(line)
		email = extract_email(sender)
		if email:
			emails.append(email)
	print(emails)
	print(f"emails count: {len(emails)}")
