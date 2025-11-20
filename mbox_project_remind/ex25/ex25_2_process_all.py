import sys
import mailbox
import re
import time

# 経過時間のモニタリングメッセージ（100通ごと）
# 総メール数
# recipient宛メール数
# ユニークドメイン数
# Total処理時間
# トップ10 送信数のドメイン ★

def	dict_domain(domain):
	if domain:
		domains_dict[domain] = domains_dict[domain].get(domain, 0) + 1

def	ext_domain(sender):
	if sender:
		try:
			domain = sender.split("@")[1]
			return domain
		except IndexError as a:
			print(f"Index error detected {a}")
		except Exception as a:
			print(f"Unexpected error detected {a}")

def	ext_sender(from_line):
	if from_line:
		sender = re.search(r"[\w\.-]+@[\w\.-]+", from_line)
		if sender:
			return sender.group()
		return None

def	is_for_rcpt(to_line):
	if to_line:
		matched = re.search(rf"\w+@{recipient}", to_line)
		if matched:
			return True
		return False

def	time_monitor(current_time, last_time, start_time):
	if current_time - last_time >= 0.1:
		elapsed = current_time - start_time
		print(f"Processing... mail {idx}: {elapsed:.1f}s", end='\r', flush=True)
		return current_time

def	progress_monitor(idx, start_time):
	if idx % 100 == 0:
		prog_time = time.time() - start_time
		print(f"{idx} mails completed: {prog_time}s")

def	print_result(idx, total_time, domains_dict, rcpt_count):
	sorted_domains = sorted(domains_dict.items(), key=lambda x: x[1], reverse=True)
	print("=== Result ===")
	print(f"Total number of mail: {idx}")
	print(f"Number of sent to {recipient}: {rcpt_count}")
	print(f"Number of unique domain: {len(domains_dict)}")
	# トップ10 ドメインを表示

if len(sys.argv) != 3:
	print("Expected arguments: [this file] [file_name.mbox] [recipient domain]")
	print(f"argv len: {len(sys.argv)}")
	sys.exit(1)
else:
	file_name = sys.argv[1]
	recipient = re.escape(sys.argv[2])
	mbox = mailbox.mbox(file_name)
	domains_dict = {}
	with open(file_name, "r", encoding="utf=8", error="ignore") as file:
		start_time = time.time()
		last_time = start_time
		rcpt_count = 0
		for idx, mails in enumerate(mbox, 1):
			current_time = time.time()
			bool_rcpt = is_for_rcpt(mbox["to"])
			last_time = time_monitor(current_time, last_time, start_time)
			progress_monitor(idx, start_time)
			if bool_rcpt:
				rcpt_count += 1
			sender = ext_sender(mbox["from"])
			domain = ext_domain(sender)
			dict_domain(domain)
		total_time = current_time - start_time
		print_result(idx, total_time, domains_dict, rcpt_count)





# emailオブジェクト（オブジェクトって具体的な定義何だっけ？）はenumerate()でイテレートできない？
# ex25_1でも使っているemail. とか mailbox.mboxとかってライブラリにある道具に直接渡すってこと？
# -mailbox.mbox()はどっちの単語も緑色になるけど、二つ使っている？
