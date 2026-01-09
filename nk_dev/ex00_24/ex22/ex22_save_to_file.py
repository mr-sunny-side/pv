import re
import sys

def	process_sender(sender, matched):
	if sender and matched:
		ext_to_index_domain(sender)
		return True
	return False

def	reset_variable():
	return None, None

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
	# if line:
	# 	if line.startswith("From "):
	# 		return True
	# 	return False
	return line and line.startswith("From ")
	# 真偽の判断をしてるだけなので「短絡評価」でいい

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
	# return line and line.startswith("From: ")
	# conf_start()と同じに見えるが、
	# この関数はext_to_index_domain(line)の為に、必ずNoneかlineを返す必要がある
	# 今の設計だと、自動的に関数が連なって呼び出されるので、バグの発見が難しい

if len(sys.argv) != 3:
	print("number of arguments must be 3")
	print(f"argv len: {len(sys.argv)}")
	sys.exit(1)
else:
	file_name = sys.argv[1]
	filter_receiver = re.escape(sys.argv[2])
	senders_domain = {}
	# re.escape()が必要になるのは、正規表現の場合に記号が含まれる場合のみ
	# 引数として渡すなら、文字列扱いなのでいい（多分）
	with open(file_name, "r") as file:

		matched = None
		sender = None
		for line in file:
			line = line.rstrip()
			tmp_matched = conf_receiver(line)
			tmp_sender = conf_sender(line)
			# 関数の無駄な呼び出しを回避している
			if conf_start(line):
				process_sender(sender, matched)
				sender, matched = reset_variable()
			if tmp_sender:
				sender = tmp_sender
			if tmp_matched:
				matched = tmp_matched
		process_sender(sender, matched)
	with open("senders.txt", "w") as file:
		print("result...")
		file.write("result...\n")
		for domain, count in senders_domain.items():
			output_line = f"domain: {domain}...{count}"
			print(output_line)
			file.write(output_line + "\n")
