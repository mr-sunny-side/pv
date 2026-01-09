import re
import sys
import csv

def	process_list(sender, recipient, mail_count):
	# 最後にsenderとmatchedの値をリセットする
	if sender and recipient:
		# ext_sender()で抽出したアドレス（戻り値）を再代入
		# その上でext_domain_to()に渡す
		sender = ext_sender_to(sender)
		ext_domain_to(sender)
		mail_count_list.append(mail_count)
	return None, None

def	list_sender(line):
	if line:
		sender_list.append(line)
		return line
	return None

def	list_recipient(line):
	if line:
		recipient_list.append(line)
		return line
	return None

def	list_domain(line):
	if line:
		domain_list.append(line)
		return line
	return None

def	ext_sender_to(line):
	if line:
		matched = re.search(r"[\w\.-]+@[\w\.-]+", line)
		if matched:
			return list_sender(matched.group())
		else:
			# 正規表現マッチ失敗時、元のlineを保存してリスト不整合を防ぐ
			print(f"dose'nt matched mail:{mail_count} line:{line}")
			return list_sender(line)
	return None

def	ext_domain_to(line):
	if line:
		try:
			domain = line.split("@")[1]
			return list_domain(domain)
		except IndexError:
			print(f"couldn't split mail:{mail_count} line:{line}")
			return list_domain("PARSE_ERROR")

def	conf_start(line):
	return line and line.startswith("From ")

def	conf_sender(line):
	# 設計上、conf_senderはbool型を返してはいけない
	if line:
		if line.startswith("From: "):
			return line
		return None

def	conf_recipient_to(line):
	if line:
		matched = re.search(rf"\w+@{recipient}", line)
		if line.startswith("To: ") and matched:
			return list_recipient(matched.group())
	return None

if len(sys.argv) != 3:
	print("except argument:")
	print("{this file} {.mbox file} {recipient}")
	print(f"inputted argument len: {len(sys.argv)}")
	sys.exit(1)
else:
	sender_list = []
	recipient_list = []
	domain_list = []
	recipient = re.escape(sys.argv[2])
	file_name = sys.argv[1]
	mail_count_list = []
	mail_count = -1
	sender = None
	recipe_holder = None
	with open(file_name, "r") as file:
		for line in file:
			line = line.rstrip()
			# 判定のために、tmpが必要
			# 判定が通ったら、それぞれの変数に代入する
			tmp_sender = conf_sender(line)
			tmp_r_holder = conf_recipient_to(line)
			if conf_start(line):
				mail_count += 1
				sender, recipe_holder = process_list(sender, recipe_holder, mail_count)
			if tmp_sender:
				sender = tmp_sender
			if tmp_r_holder:
				recipe_holder = tmp_r_holder
		mail_count += 1
		process_list(sender, recipe_holder, mail_count)

	with open("senders.csv", "w", newline='') as file:
		writer = csv.writer(file)
		writer.writerow(["mail_count", "sender", "domain", "recipient"])
		for count, sender, domain, recipient in zip(mail_count_list, sender_list, domain_list, recipient_list):
			writer.writerow([count, sender, domain, recipient])
			print(f"{count}, {sender}, {domain}, {recipient}")

# 各ext関数が失敗した場合、リスト長が不均一になってしまうので、そのエラーハンドリング
# open関数のmatched変数は、実際にはbool型ではないので、変数名を修正
# 40行目のエラーハンドリングでは、リスト不整合が修正できないので、要改善
