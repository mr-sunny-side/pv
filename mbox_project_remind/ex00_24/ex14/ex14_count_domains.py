import re

domains_count = {}

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
		# if domain and domain in domains_count:
		# 	domains_count[domain] += 1
		# elif domain:
		# 	domains_count[domain] = 1

		# get()を使ってkeyの有無を簡潔に調べる方法
		if domain:
			domains_count[domain] = domains_count.get(domain, 0) + 1

	for domain, count in domains_count.items():
		print(f"domain: {domain}, domain counts: {count}")
