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

def	conf_receiver(line):
	if line:
		matched = re.search(rf"\w+@{filter_receiver}", line)
		if line.startswith("To: ") and matched:
			return True
		return False

def	conf_to_ext_sender(line):
	if line:
		if line.startswith("From: "):
			return ext_sender(line)
		return None

if len(sys.argv) != 3:
	print("number of argument is incorrect")
	sys.exit(1)
else:
	file_name = sys.argv[1]
	filter_receiver = re.escape(sys.argv[2])
	sender = None
	matched = None
	with open(file_name, "r") as file:
		for line in file:
			if conf_start(line):
				sender, matched = print_sender(sender, matched)
			if conf_to_ext_sender(line):
				sender = conf_to_ext_sender(line)
			if conf_receiver(line):
				matched = conf_receiver(line)
		print_sender(sender, matched)
