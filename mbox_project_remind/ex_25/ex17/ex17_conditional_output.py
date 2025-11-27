import re
sender = None
match = None

def	conf_start(line):
	if line:
		if line.startswith("From "):
			return True
		return None

def	conf_digit(line):
	match = re.search(r"\w+@digitalgeek.tech", line)
	if line:
		if line.startswith("To: ") and match:
			return True
		return None

def	ext_sender(line):
	match = re.search(r"[\w\.-]+@[\w\.-]+", line)
	if line:
		if match:
			return match.group()
		else:
			print(f"couldn't extract '{line}'")
			return line

def	conf_sender(line):
	if line:
		if line.startswith("From: "):
			return ext_sender(line)
		return None

with open("sample.mbox", "r") as file:
	for line in file:
		line = line.rstrip()
		if conf_start(line):
			if match and sender:
				print(sender)
				sender = None
				match = None
		if conf_sender(line):
			sender = conf_sender(line)
		if conf_digit(line):
			match = conf_digit(line)
	if match and sender:
		print(sender)
