import sys
import re
import mailbox
from email.utils import parsedate_to_datetime
from datetime import datetime

domains_dict = {}

# DRY原則（Don't Repeat Yourself）に則り、最低限のデータのみ保存
# 単一責任も考慮
class DomainDate:
	def	__init__(self):
		self.date = []

	def	add_date(self, date_obj):
		self.date.append(date_obj) if date_obj else None

def	ext_domain(from_line):
	if from_line:
		try:
			raw_domain = from_line.split('@')[1]
			domain = re.search(r"[\w\.-]+", raw_domain)
			return domain.group()
		# 変数名は慣習に従い{e}とする
		except IndexError as e:
			print(e)
			return "Index Error"
		except Exception as e:
			print(e)
			return "Unexpected Error"

if len(sys.argv) != 3:
	sys.exit(1)
else:
	file_name = sys.argv[1]
	output_dir = sys.argv[2]
	mbox = mailbox.mbox(file_name)

	for idx, mails in enumerate(mbox, 1):
		# if idx > 30:
		# 	break
		domain = ext_domain(mails['From'])
		if domain not in domains_dict:
			domains_dict[domain] = DomainDate()

		date_obj = parsedate_to_datetime(mails['Date'])
		domains_dict[domain].add_date(date_obj)

	with open(f"{output_dir}/ex25_3a.txt", "w") as file:

		title = '=' *3 + 'Mails Date Info' + '=' *3
		print(title)
		file.write('\n' + title + '\n')

		# 見やすい出力フォーマットにした
		for domain, date_info in domains_dict.items():
			print(domain)
			file.write('\n' + domain + '\n')
			for date_obj in date_info.date:

				str_format = date_obj.strftime("%Y-%m-%d")
				iso_format = date_obj.isoformat()
				print(f"	{str_format} | {iso_format}")
				file.write(f"	{str_format} | {iso_format}\n")

# isoformat関数を使って、辞書内オブジェクト（self.iso_format）にISO形式の日にちを保存する
# - completed
