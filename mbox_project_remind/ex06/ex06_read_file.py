import re

with open("sample.mbox", "r") as file:
	for line in file:
		print(line.rstrip())
