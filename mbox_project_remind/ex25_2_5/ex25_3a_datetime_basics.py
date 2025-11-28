import sys
import re
import mailbox
from email.utils import parsedate_to_datetime
from datetime import datetime

domains_dict = {}

class DomainDate:
	def	__init__(self):
		self.raw_date = []
		self.date_str = []

	def	add_date(self, date_obj):
		self.raw_date.append(date_obj)
		date_str = date_obj.strftime("%Y-%m-%d")
		self.date_str.append(date_str)

def	ext_domain(from_line):
	if from_line:
		try:
			raw_domain = from_line.split('@')[1]
			domain = re.search(r"[\w\.-]+", raw_domain)
			return domain.group()
		except IndexError as a:
			print(a)
			return "Index Error"
		except Exception as a:
			print(a)
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

		for domain, date_info in domains_dict.items():
			print(domain)
			file.write('\n' + domain + '\n')
			for date_str in date_info.date_str:
				print('	' + date_str)
				file.write('	' + date_str + '\n')
			for raw_date in date_info.raw_date:
				print('	' + raw_date)
				file.write('	' + raw_date + '\n')

# isoformat関数を使って、辞書内オブジェクト（self.raw_date）にISO形式の日にちを保存する
