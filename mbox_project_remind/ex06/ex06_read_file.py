import re

with open("sample.mbox", "r") as file:
	for line in file:
		line = line.rstrip()
		print(line)
