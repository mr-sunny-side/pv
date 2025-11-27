import re

with open("sample.mbox", "r") as file:
	for line in file:
		line = line.rstrip()
		print(line)

#pythonの変数はイミュータブル（変更不可）なので、
#値を変更したらもう一度代入する必要がある
