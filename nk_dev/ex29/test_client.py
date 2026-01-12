#!/usr/bin/env python3

import time
import socket

# サーバーからメッセージを待つ関数(別スレッド)
def	receive_message():
	try:
		while True:
			message_bytes = client_socket.recv(1024)

			# 送信が空なら切断なので、プログラムを終了
			# これは別スレッドなので、ループを抜けてもメインスレッドが動き続けてしまう
			# なのでsys.exit(0)を明記
			if not message_bytes:
				print('Server closed the connection')
				sys.exit(0)

			# デコード
			message = message_bytes.decode('utf-8', errors='replace')
			
			# 送信が特殊文字だけなら無視
			if not message.strip():
				continue
			
			print(message)
	# エラーの場合システムを終了
	except Exception as e:
		print('ERROR receive_message: {e}')
		sys.exit(1)

def	

def	main():

	
