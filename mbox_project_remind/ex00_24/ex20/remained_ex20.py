import re
import sys

def	print_sender(sender, matched):
	if sender and matched:
		print(sender)
	return None,None

def	ext_sender(line):
	if line:
		matched = re.search(r"[\w\.-]+@[\w\.-]+", line)
		if matched:
			return matched.group()
		return None

def	conf_start(line):
	if line:
		if line.startswith("From "):
			return True
		return False

def	conf_digit(line):
	if line:
		matched = re.search(r"\w+@digitalgeek.tech", line)
		# これだとdigitalgeek(任意の一文字)techという意味になる
		# digitalgeek\.techと書くかre.escape()を使う必要がある
		if line.startswith("To: ") and matched:
			return True
		return False

def	conf_to_ext_sender(line):
	if line:
		if line.startswith("From: "):
			return ext_sender(line)
		return None

if len(sys.argv) != 2:
	print("number of argument is incorrect")
	sys.exit(1)
else:
	file_name = sys.argv[1]
	sender = None
	matched = None
	with open(file_name, "r") as file:
		for line in file:
			if conf_start(line):
				sender, matched = print_sender(sender, matched)
			if conf_to_ext_sender(line):
				sender = conf_to_ext_sender(line)
			if conf_digit(line):
				matched = conf_digit(line)
		print_sender(sender, matched)
