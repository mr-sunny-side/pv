import re

# 関数内で特殊様式に対する対応を行う
# with open関数でファイルを開いて実行
# for line in fileでループ
# if文で("From:")から始まる行を特定
# print関数で出力

# def extract_email(line):
# 	match =  re.search(r'<(.+?)>', line)
# 	# 出力は関数外で行い、柔軟性を上げる
# 	if match:
# 		sender = match.group(1)
# 		print(f"送信者: {sender}")
# 	elif line.startswith("From:"):
# 		# with open関数で既に判定しているので、ここはelseでいい
# 		parts = line.split()
# 		print(f"送信者: {parts[1]}")
# 	return None

# with open('sample.mbox', 'r') as file:
# 	for line in file:
# 		if line.startswith("From:"):
# 			extract_email(line)

# From:を抽出するコード（To:解析無し）
# 単一責任の原則

def extract_email(line):
	match = re.search(r'<(.+?)>', line)
	if match:
		return (match.group(1))
	else:
		parts = line.split()
		return (parts[1])
	return None

# with open('sample.mbox', 'r') as file:
# 	for line in file:
# 		if line.startswith("From:"):
# 			email = extract_email(line)
# 			if email:
# 				print(f"送信者: {email}")



# Claudeの実装例
# 上記のextract_email関数はそのまま残す

def process_email(sender, matched):
    """蓄積した情報から判定して出力する"""
    if matched and sender:
        print(f"digitalgeek.tech宛の送信者: {sender}")

# メールを解析する
sender = None
matched = False

with open('sample.mbox', 'r') as file:
    for line in file:
        line = line.strip()  # 行末の改行を削除

        if line.startswith("From "):
            # 前のメールを判定
            process_email(sender, matched)
            # リセット
            sender = None
            matched = False

        elif line.startswith("From:"):
            sender = extract_email(line)

        elif line.startswith("To:") and "@digitalgeek.tech" in line:
            matched = True

    # ファイルの最後のメールも判定
    process_email(sender, matched)
