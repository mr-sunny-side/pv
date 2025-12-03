with open("sample.mbox", "r") as file:
	for line in file:
		line = line.rstrip()
		#rstripの行を、下のif文の中に入れて処理を減らすこともできる
		if line.startswith("From: "):
			print(line)

# →しかし、if文の外に置くことで、複雑なコードになったとき、圧倒的に保守しやすい
		# →mallocみたいな、慎重な扱いが求められる関数でない限り、
		# →基本的には「読みやすさ・保守しやすさ」が求められる
		# ※早すぎる最適化は諸悪の根源 (Donald Knuth)
