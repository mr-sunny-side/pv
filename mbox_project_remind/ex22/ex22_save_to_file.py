import re
import sys

def	process_sender(sender, matched):
	if sender and matched:
		ext_to_index_domain(sender)
	return None, False



def	index_domain(line):
	if line:
		try:
			domain = line.split("@")[1]
			senders_domain[domain] = senders_domain.get(domain, 0) + 1
			return True
		except IndexError:
			print(f"couldn't split domain: {line}")
			senders_domain[line] = senders_domain.get(line, 0) + 1
			return False

def	ext_to_index_domain(line):
	if line:
		matched = re.search(r"[\w\.-]+@[\w\.-]+", line)
		if matched:
			return index_domain(matched.group())
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

def	conf_sender(line):
	if line:
		if line.startswith("From: "):
			return line
		return None

if len(sys.argv) != 3:
	print("number of arguments must be 3")
	print(f"argv len: {len(sys.argv)}")
	sys.exit(1)
else:
	senders_domain = {}
	matched = False
	sender = None
	file_name = sys.argv[1]
	# re.escape()が必要になるのは、正規表現の場合に記号が含まれる場合のみ
	# 引数として渡すなら、文字列扱いなのでいい（多分）
	filter_receiver = re.escape(sys.argv[2])
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

	with open("senders.txt", "w") as file:
		print("result...")
		file.write("result...\n")
		for domain, count in senders_domain.items():
			output_line = f"domain: {domain}...{count}"
			print(output_line)
			file.write(output_line + "\n")
