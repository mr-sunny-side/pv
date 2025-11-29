import sys
import re
import mailbox
from email.utils import parsedate_to_datetime
from datetime import datetime

# **digitalgeek.tech宛のメールについて
#	各送信者ドメインの以下の情報を収集せよ**。

# - メール数
# - 最初の受信日
# - 最後の受信日
# - 日数の差（last - first）

class DomainDate:
	def	__init__(self):

		self.count = 0
		self.first_date = None
		self.last_date = None

	def	add_date(self, date_obj):

		# ifは必ず検証するが、elifはifが真なら通過してしまう
		self.count += 1
		if not self.first_date or self.first_date > date_obj:
			self.first_date = date_obj
		if not self.last_date or self.last_date < date_obj:
			self.last_date = date_obj

	def	diff_date(self):

		result = self.last_date - self.first_date
		return result

def	ext_domain(from_line):
	if from_line:
		try:
			rough_cut = from_line.split("@")[1]
			domain = re.search(r"[\w\.-]+", rough_cut)
			return domain.group()
		except IndexError as e:
			print(f"{from_line}\n{e}")
			return "Index Error"
		except Exception as e:
			print(f"{from_line}\n{e}")
			return "Unexpected Error"

def	conf_rcpt(to_line):
	if to_line and recipient in to_line:
		return True
	return False

if len(sys.argv) != 4:
	print("Arguments Error")
	sys.exit(1)
else:
	domains_date = {}
	file_name = sys.argv[1]
	output_dir = sys.argv[2]
	recipient = sys.argv[3]
	mbox = mailbox.mbox(file_name)
	for mails in mbox:
		from_line = mails['From']
		to_line = mails['To']
		domain = ext_domain(from_line)
		if not conf_rcpt(to_line):
			continue
		if domain not in domains_date:
			domains_date[domain] = DomainDate()

		date_line = mails['Date']
		date_obj = parsedate_to_datetime(date_line)
		domains_date[domain].add_date(date_obj)

	with open(f"{output_dir}/ex25_3b.txt", "w") as file:
		title_length = 3
		title = '=' *title_length + 'Date Statistics by Domain' + '=' *title_length
		# 辞書構造のインスタンスにおける、sorted関数の記述
		sorted_dict = sorted(domains_date.items(), key=lambda x: x[1].count, reverse=True)

		print(title)
		file.write(f"{title}\n")
		# sorted関数はlistでタプルを返すので、items()は使わない
		for domain, domain_info in sorted_dict:
			first_date_str = domain_info.first_date.strftime("%Y-%m-%d")
			last_date_str = domain_info.last_date.strftime("%Y-%m-%d")

			print(domain)
			file.write(f"{domain}\n")
			print(f"	Mail Count: {domain_info.count}")
			file.write(f"	Mail Count: {domain_info.count}\n")
			print(f"	First Date: {first_date_str}")
			file.write(f"	First Date: {first_date_str}\n")
			print(f"	Last Date: {last_date_str}")
			file.write(f"	Last Date: {last_date_str}\n")

			delta = domain_info.diff_date()
			delta_str = str(delta.days)
			print(f"	Interval: {delta_str} Days")
			file.write(f"	Interval: {delta_str} Days\n")
