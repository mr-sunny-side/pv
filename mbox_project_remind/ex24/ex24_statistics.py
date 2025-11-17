# - 総メール数: count変数
# - digitalgeek.tech宛のメール数: matched_count変数で記録
# - ユニークな送信者ドメイン数: domain_dict辞書のkey数を出力
# - 最も多くメールを送信しているドメイン: domain_dictからmax関数で出力

import re
import sys
import csv

def	process_mail(sender, matched, matched_count):
	if sender and matched:
		matched_count += 1
		ext_sender_to(sender)
	return None, None, matched_count

def	dict_domain(line):
	if line:
		domain_dict[line] = domain_dict.get(line, 0) + 1
	return line

def	ext_domain_to(line):
	if line:
		try:
			domain = line.split("@")[1]
			return dict_domain(domain)
		except IndexError:
			print(f"dose'nt split mail:{mail_count} line:{line}")
			error_dict[line] = error_dict.get(line, 0) + 1
			return dict_domain("split_error")

def	ext_sender_to(line):
	if line:
		matched = re.search(r"[\w\.-]+@[\w\.-]+", line)
		if matched:
			return ext_domain_to(matched.group())
		else:
			print(f"dose'nt matched mail:{mail_count} line:{line}")
			error_dict[line] = error_dict.get(line, 0) + 1
			return dict_domain("extract_error")

def	conf_rcpt(line):
	if line:
		matched = re.search(rf"\w+@{recipient}", line)
		return matched

def	conf_sender(line):
	# 設計上、当関数はbool型を返せない
	if line:
		if line.startswith("From: "):
			return line
		return None

def	conf_start(line):
	return line and line.startswith("From ")

if len(sys.argv) != 3:
	print("excepted argument: {this file} {.mbox} {recipient domain}")
	print(f"argument len {len(sys.argv)}")
	sys.exit(1)
else:
	recipient = re.escape(sys.argv[2])
	file_name = sys.argv[1]
	matched_count = 0
	mail_count = -1
	error_dict = {}
	domain_dict = {}
	sender = None
	matched = None
	with open(file_name, "r") as file:
		for line in file:
			line = line.rstrip()
			tmp_sender = conf_sender(line)
			tmp_matched = conf_rcpt(line)
			if conf_start(line):
				mail_count += 1
				sender, matched, matched_count = process_mail(sender, matched, matched_count)
			if tmp_sender:
				sender = tmp_sender
			if tmp_matched:
				matched = tmp_matched
		mail_count += 1
		process_mail(sender, matched, matched_count)

	with open("result_ex24.csv", "w", newline='') as file:
		# re.escape()すると、標準出力に \ が干渉するので、再定義する
		recipient = sys.argv[2]
		writer = csv.writer(file)
		writer.writerow(["mail_count", "matched_count", "unique_domain_count", "frequent_domain_count"])
		unique_domain = len(domain_dict)
		frequent_domain = max(domain_dict, key=domain_dict.get)
		writer.writerow([mail_count, matched_count, unique_domain, frequent_domain])
		print("analytics...")
		print(f"{'total mails:':<30} {mail_count:>15}")
		# print(f"{'matched ' +recipient+ ' count:':<30} {matched_count:>15}")
		print(f"matched {recipient} count:{matched_count:>15}")
		print(f"{'unique domain count:':<30} {unique_domain:>15}")
		print(f"{'frequent domain:':<30} {frequent_domain:>15}")
