with open("sample.mbox", "r") as file:
	for line in file:
		if line.startswith("From: "):
			line = line.rstrip()
			print(line)
