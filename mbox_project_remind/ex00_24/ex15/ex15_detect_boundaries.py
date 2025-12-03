email_count = 0

with open("sample.mbox", "r") as file:
	for line in file:
		if line.startswith("From "):
			email_count += 1
			print(f"メール #{email_count} 開始")
