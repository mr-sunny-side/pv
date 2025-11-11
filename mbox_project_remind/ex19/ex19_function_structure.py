import re

def	process_email(sender, matched):
	if sender and matched:
		return True
	return False

def	ext_sender(line):
	matched = re.search(r"[\w\.-]+@[\w\.-]+", line)
	if line:
		if matched:
			return matched.group()
		else:
			print(f"couldn't extract '{line}")
			return line

def	conf_start(line):
	if line:
		if line.startswith("From "):
			return True
		return False

def	conf_sender(line):
	if line:
		if line.startswith("From: "):
			return ext_sender(line)
		return None

def	conf_digit(line):
	matched = re.search(r"\w+@digitalgeek.tech", line)
	if line:
		if matched:
			return True
		return False

with open("sample.mbox", "r") as file:
	sender = None
	matched = None
	for line in file:
		line = line.rstrip()
		if conf_start(line):
			if process_email(sender, matched):
				print(sender)
				sender = None
				matched = None
			# sender, matched = process_email(sender, matched)
				# .pyではダプル(tuple)というデータ構造を返せる
				# これを展開(unpacking)して、二つの変数を初期化することが可能
				# ただし、この書き方だと単一責任を逸脱するので、あまりよくない
				# ※bool変数はiterable(複数の要素を格納する物)ではないので、この書き方になる
		if conf_sender(line):
			sender = conf_sender(line)
		if conf_digit(line):
			matched = conf_digit(line)
	if process_email(sender, matched):
		print(sender)
