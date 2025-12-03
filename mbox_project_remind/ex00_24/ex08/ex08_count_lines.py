with open("sample.mbox", "r") as file:
	count = 0
	for line in file:
		line = line.rstrip()
		if line.startswith("From "):
			count += 1
	print(f"メール数: {count}")
