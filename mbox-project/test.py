line = "From: notifications@github.com"

# startswith,split関数の学習
print("test0\n")

if line.startswith("From:"):
	parts = line.split()
	sender = parts[1]
	print("送信者は:", sender)

line2 = 'From: "Slack Notifications" <notifications@slack.com>'

if line2.startswith("From:"):
	parts2 = line2.split()
	print("分割結果:", parts2)
	print("要素数:", len(parts2))
	print("parts2[1]は:", parts2[1])

import re

line2 = 'From: "Slack Notifications" <notifications@slack.com>'

# search関数の学習
print("\ntest1\n")

match = re.search(r'<(.+?)>', line2)
if match:
	email = match.group(1)
	print("メールアドレス:", email)
else:
	parts = line2.split()
	email = parts[1]
	print("メールアドレス:", email)

# メールアドレスの抽出関数の作成
print("\ntest2\n")

def extract_email(line):
	match = re.search(r"<(.+?)>", line)
	if (match):
		return match.group(1)
	else:
		parts = line.split()
		if len(parts) >= 2:
			return parts[1]
	return None

test_lines = [
	"From: notifications@github.com",
	'From: "slack Notifications" <notifications@slack.com>',
	"From: billing@aws.amazon.com"
]

for line in test_lines:
	email = extract_email(line)
	print(f"入力: {line}")
	print(f"結果: {email}")
	print()

# greedyの学習
print("\ngreedy test\n")

text = "<email1@example.com> and <email2@example.com>"

greedy = re.search(r'<(.+)>', text)
print("greedy:", greedy.group(1))

non_greedy = re.search(r'<(.+?)>', text)
print("non greedy:", non_greedy.group(1))

# f-stringの学習
