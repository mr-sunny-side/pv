import sys
import re
import mailbox
from email.utils import parsedate_to_datetime
from datetime import datetime

domains_dict = {}

class DomainDate:
	def	__init__(self):
		self.iso_format = []
		self.string_format = []

	def	add_date(self, date_obj):
		iso_formatted = date_obj.isoformat()
		self.iso_format.append(iso_formatted)

		string_formatted = date_obj.strftime("%Y-%m-%d")
		self.string_format.append(string_formatted)

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
			for string_format in date_info.string_format:
				print('	' + string_format)
				file.write('	' + string_format + '\n')
			for iso_format in date_info.iso_format:
				print('	' + iso_format)
				file.write('	' + iso_format + '\n')

# isoformat関数を使って、辞書内オブジェクト（self.iso_format）にISO形式の日にちを保存する
# - completed
