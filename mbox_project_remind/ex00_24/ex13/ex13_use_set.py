import re

domains = set()

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


def	extract_domain(line):
	if line:
		try:
			return line.split("@")[1]
		except IndexError:
			return None

with open("sample.mbox", "r") as file:
	for line in file:
		line = line.rstrip()
		sender = extract_sender(line)
		email = extract_email(sender)
		domain = extract_domain(email)
		if domain:
			domains.add(domain)
	print(domains)
	print(f"domains count: {len(domains)}")
