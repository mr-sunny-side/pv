import sys
import re
import email
from email import policy

def	is_start(line):
	return line and line.startswith("From ")

def	ext_domain(line):
	if line:
		try:
			domain = line.split("@")[1]
			return domain
		except IndexError:
			print(f"couldn't strip {line}")
			return line

def	ext_sender_to(line):
	if line:
		sender = re.search(r"[\w\.-]+@[\w\.-]+", line)
		if sender:
			return ext_domain(sender.group())
		else:
			print(f"couldn't extract sender {line}")
			return line

if len(sys.argv) != 2:
	print("excepted arguments: [this file] [.mbox]")
	print(f"argv len: {len(sys.argv)}")
	sys.exit(1)
else:
	file_name = sys.argv[1]
	mail_lines = []
	with open(file_name, "r", encoding="utf-8", errors="ignore") as file:
		start_count = 0
		for line in file:
			if is_start(line):
				start_count += 1
			elif start_count >= 2:
				break
			mail_lines.append(line)

		mail_text = "".join(mail_lines)
		msg = email.message_from_string(mail_text, policy=policy.default)
		domain = ext_sender_to(msg['from'])
		sender = msg['from']
		recipient = msg['to']
		subject = msg['subject']
		# 辞書のkeyの参照
		# print(f"{msg.keys()}")
		date = msg['date']

		print("=== メール情報 ===")
		print(f"{'送信者:':<15}{sender:>90}")
		print(f"{'受信者:':<15}{recipient:>90}")
		print(f"{'件名:':<15}{subject:>90}")
		print(f"{'送信日時:':<15}{date:>90}")
		print(f"{'送信者ドメイン:':<15}{domain:>90}")

# 毎回stripとsplitを間違えるので、英単語の意味を含めて理解するべき
# 今回はwordpressのメールで、送信ドメインが所有者ドメインと一致するパターンだった。
# ーこういうのも考慮対象かもしれない。
# :<~ はバイト数カウントなので、日本語出力なら別のライブラリを参照する必要があるらしい
