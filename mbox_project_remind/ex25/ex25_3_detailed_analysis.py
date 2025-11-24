import sys
import time
import mailbox
from datetime import datetime
from email.utils import parsedate_to_datetime

# - メール数
# - 最初の受信日
# - 最後の受信日
# - 代表的な件名（最も頻繁な件名トップ3）
# - 平均メール間隔（日数）
# ※ 練習の為、time.time()も利用

# mailboxでmboxオブジェクトを作成
# for文でmailsとして1通ずつ取り出す
# DomainInfoクラスで各ドメインインスタンスを作成
# csv.writerで出力

# -クラスの構造
# __info__でdomains_dict内のインスタンスを定義
# その他クラス内関数で計算

# 11-24: 後はcsv出力を記述

class DomainInfo:
	def	__init__(self):
		self.count = 0
		self.first_date = None
		self.last_date = None
		self.subject = {}

	def	add_mail(self, date_obj, subject):
		self.count += 1
		self.subject[subject] = self.subject.get(subject, 0) + 1

		if not self.first_date or date_obj < self.first_date:
			self.first_date = date_obj
		elif not self.last_date or date_obj > self.last_date:
			self.last_date = date_obj

	def	top3_subject(self, n=3):
		sorted_subject = sorted(self.subject.items, key=lambda x: x[1], reverse=True)
		return sorted_subject[:n]

	def	get_average_interval(self):
		if self.first_date and self.last_date and self.count > 1:
			interval = self.last_date - self.first_date
			return interval / (self.count - 1)
		return 0

def	time_monitor(last_update, current_update, prog_start, idx):
	if current_update - last_update > 0.1:
		elapsed = current_update - prog_start
		print(f"Processing...mail:{idx} {elapsed:.1f}", end='\r', flush=True)
		return current_update
	return last_update

def	progress_monitor(prog_start, current_update, idx):
	if idx % 100 is 0:
		elapsed = current_update - prog_start
		print(f"{idx}mails complete {elapsed:.1f}" + " " * 20)

def	ext_domain(from_line):
	try:
		domain = from_line.split('@')[1].rstrip('>')
		return domain
	except IndexError as a:
		print(f"Index error detected: {a}")
	except Exception as a:
		print(f"Unexpected error detected: {a}")

def	conf_rcpt(to_line):
	if to_line:
		return recipient in to_line
	return False

file_name = sys.argv[1]
recipient = sys.argv[2]
mbox = mailbox.mbox(file_name)
prog_start = time.time()
last_update = prog_start
domains_dict = {}

if len(sys.argv) is not 3:
	sys.exit(1)
else:
	for idx, mails in enumerate(mbox, 1):
		current_update = time.time()
		last_update = time_monitor(last_update, current_update, prog_start, idx)
		progress_monitor(prog_start, current_update, idx)

		to_line = mails['to']
		domain = ext_domain(mails['from'])
		if not conf_rcpt(to_line):
			continue
		if not domain:
			continue
		elif domain not in domains_dict:
			domains_dict[domain] = DomainInfo()

		date_line = mails['date']
		date_obj = parsedate_to_datetime(date_line) if date_line else None
		subject = mails['subject'] or '(no subject)'
		domains_dict.add_mail(domain, date_obj, subject)
