import re
import sys

def	process_sender(sender, matched):
	if sender and matched:
		ext_to_index_domain(sender)
	return None,None

def	index_domain(line):
	if line:
		senders_domain[line] = senders_domain.get(line, 0) + 1
		# domain, count = senders_domain.items(line)
		# items.()は引数を取らず、ループ処理に用いる
		# count = senders_domain[line]
		# print(f"index {domain}...count{count}")
		return True
	return False

def	ext_to_index_domain(line):
	if line:
		matched = re.search(r"[\w\.-]+@[\w\.-]+", line)
		try:
			if matched:
				return index_domain((matched.group()).split("@")[1])
		except IndexError:
			print("couldn't split sender address")
			return index_domain(line)

# def	ext_sender(line):
# 	if line:
# 		matched = re.search(r"[\w\.-]+@[\w\.-]+", line)
# 		if matched:
# 			return matched.group()
# 		return None

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

def	conf_sender(line):
	if line:
		if line.startswith("From: "):
			return line
		return None

if len(sys.argv) != 3:
	print("number of argument is incorrect")
	sys.exit(1)
else:
	file_name = sys.argv[1]
	filter_receiver = re.escape(sys.argv[2])
	senders_domain = {}
	sender = None
	matched = None
	with open(file_name, "r") as file:
		for line in file:
			line = line.rstrip()
			if conf_start(line):
				sender, matched = process_sender(sender, matched)
			if conf_sender(line):
				sender = conf_sender(line)
			if conf_receiver(line):
				matched = conf_receiver(line)
		process_sender(sender, matched)
		print("result...")
		for domain, count in senders_domain.items():
			print(f"domain: {domain}...{count}")
