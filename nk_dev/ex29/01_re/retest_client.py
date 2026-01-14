#!/usr/bin/env	python3

import sys
import threading
import socket

"""
	01-14: サーバー側が接続を切ってもシステムが終了しないバグを修正

"""

# サーバーからのメッセージを受信するサブスレッド関数
# サブスレッドなのでループは関数内で行う
def	receive_message(client_socket):
	# サーバーからのメッセージを受信
	try:
		while True:
			message_bytes = client_socket.recv(1024)

			# 受信が空ならサーバー切断とみなしプログラムを終了
			if not message_bytes:
				sys.exit(0)

			# メッセージをデコード・strip()して空なら無視
			message = message_bytes.decode('utf-8', errors='replace').strip()
			if not message:
				continue

			# 受信したメッセージを出力
			print(f'/ {message}\n')

	except Exception as e:
		print(f'ERROR receive_message: {e}')
		sys.exit(1)

# サーバーにメッセージを送信
def	send_message(client_socket):
	try:
		while True:
			message = input('You: ')

			# stripしてメッセージが空文字なら無視
			if not message.strip():
				continue

			if message.strip() == 'exit':
				print('Disconnecting...')
				return

			client_socket.sendall(message.encode('utf-8', errors='replace'))

	except KeyboardInterrupt:
		print('Disconnecting...')
		return
	except Exception as e:
		print(f'ERROR send_message: {e}')
		return

def	main(host='127.0.0.1', port=8080):

	nickname = None

	# ソケット作成
	client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	# サーバーに接続
	print('Connecting...')
	client_socket.connect((host, port))
	print('Connected !')

	try:
		# ニックネームの催促
		while not nickname:
			nickname = input('Enter your nickname: ')

			#　ニックネームがから文字だったら無視
			if not nickname.strip():
				print('Warning: Nickname cannot be empty')
				continue

		# ニックネームを送信
		client_socket.sendall(nickname.encode('utf-8', errors='replace'))

		# receive_message関数をデーモンとして作成
		receive_thread = threading.Thread(
			target=receive_message,
			args=(client_socket, ),
			daemon=True
		)

		receive_thread.start()
		send_message(client_socket)

	# エラー時は異常終了
	except Exception as e:
		print(f'ERROR main: {e}')
		sys.exit(1)
	finally:
		try:
			client_socket.close()
		except:
			pass

if __name__ == '__main__':
	main()
