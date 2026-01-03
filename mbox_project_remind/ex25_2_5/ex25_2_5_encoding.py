import sys
import mailbox
from email.header import decode_header


raw_subjects = []
decoded_subjects = []

def	safe_decode_header(raw_subject):
	if raw_subject:
		parts = []
		try:
			unpacked = decode_header(raw_subject)
			for data, encoding in unpacked:
				# encodingの真偽だけで判断すると
				# - エンコード規格が不明でbyte列が出力された際にエラーとなる
				if isinstance(data, bytes):
					decoded = data.decode(encoding or 'utf-8')
				else:
					decoded = data
				parts.append(decoded)
			result = ''.join(parts)
			return result
		except UnicodeDecodeError as a:
			print(a)
			return "Decode Error"
		except TypeError as a:
			print(a)
			return "Type Error"
		except Exception as a:
			print(a)
			return "Unexpected Error"


if len(sys.argv) != 3:
	sys.exit(1)
else:
	file_name = sys.argv[1]
	output_path = sys.argv[2]
	mbox = mailbox.mbox(file_name)

	for idx, mails in enumerate(mbox, 1):
		if idx > 30:
			break
		subject = mails['subject'] or '(no subject)'
		raw_subjects.append(subject)
		decoded_subjects.append(safe_decode_header(subject))

	with open(f"{output_path}/ex25_2_5.txt", "w") as file:
		raw_sub_title = '=' *3 + 'Raw Subjects' + '=' *3
		print(raw_sub_title)
		file.write(raw_sub_title + '\n')
		for raw_sub in raw_subjects:
			print(raw_sub)
			file.write(raw_sub + '\n')

		decoded_sub_title = '=' *3 + 'Decoded Subjects' + '=' *3
		print(decoded_sub_title)
		file.write('\n' + decoded_sub_title + '\n')
		for decoded_sub in decoded_subjects:
			print(decoded_sub)
			file.write(decoded_sub + '\n')

		# all_sub_title = '=' *3 + 'All Subjects' + '=' *3
		# print(all_sub_title)
		# file.write('\n' + all_sub_title + '\n')
		# for decoded_sub in decoded_subjects:
		# 	print(decoded_sub)
		# 	file.write(decoded_sub + '\n')
