email_index = 0
sender = None
receiver = None

def	extract_sender(line):
	if line:
		if line.startswith("From: "):
			return line
		return None

def	extract_receiver(line):
	if line:
		if line.startswith("To: "):
			return line
		return None

def	conforming_email(line):
	if line:
		if line.startswith("From "):
			return True


with open("sample.mbox", "r") as file:
	for line in file:
		line = line.rstrip()
		if conforming_email(line):
			if sender and receiver:
				print(sender)
				print(receiver)
				sender = None
				receiver = None
			email_index += 1
			print(f"\nmail #{email_index} start...\n")
		if extract_sender(line):
			sender = extract_sender(line)
		if extract_receiver(line):
			receiver = extract_receiver(line)
	print(sender)
	print(receiver)
