import sys
import re

def	print_sender(sender, matched):
	if sender and matched:
		print(sender)
	return None, None

def	conf_start(line):
	if line:
		if line.startswith("From "):
			return True
		return False

def	ext_sender(line):
	matched = re.search(r"[\w\.-]+@[\w\.-]+", line)
	if line:
		if matched:
			return matched.group()
		else:
			print(f"couldn't extract '{line}'")
			return line

def	conf_sender(line):
	if line:
		if line.startswith("From: "):
			return ext_sender(line)
		return None

def	conf_digit(line):
	matched = re.search(r"\w+@digitalgeek.tech", line)
	if line:
		if line.startswith("To: ") and matched:
			return matched.group()
		return False

if len(sys.argv) != 2:
	print("argv len must be 2")
	print(f"argv's len {len(sys.argv)}")
	sys.exit(1) # errorコード(1)を返して終了させている
else:
	file_name = sys.argv[1]
	with open(file_name, "r") as file:
		matched = None
		sender = None
		for line in file:
			line = line.rstrip()
			if conf_start(line):
				sender, matched = print_sender(sender, matched)
			if conf_sender(line):
				sender = conf_sender(line)
			if conf_digit(line):
				matched = conf_digit(line)
		print_sender(sender, matched)
