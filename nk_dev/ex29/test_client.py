#!/usr/bin/env python3

import sys
import threading
import socket

# サーバーからメッセージを待つ関数(別スレッド)
def	receive_message(client_socket):
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
		print(f'ERROR receive_message: {e}')
		sys.exit(1)

# クライアントの入力を送信する関数(メインスレッド)
def	send_message(client_socket):
	try:
		while True:

			# 入力待ち状態
			message = input('You: ')

			# 空のメッセージを無視
			if not message.strip():
				continue

			# exit入力で切断
			if message.lower() == 'exit':
				print('Disconnecting...')
				break

			client_socket.sendall(message.encode('utf-8', errors='replace'))

	except KeyboardInterrupt:
		print('Disconnecting...')
	except Exception as e:
		print(f'ERROR send_message: {e}')
		return

def	main():

	client_socket = None
	host = '127.0.0.1'
	port = 8080

	nickname = None

	try:
		# ソケットを作成
		client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		# ローカルホストに接続
		print('Connecting')
		client_socket.connect((host, port))
		print('Connected !')

		# ニックネーム入力までループ
		while not nickname:
			nickname = input('Enter your nickname: ').strip()

			if not nickname:
				print('Warning: Nickname cannot be empty')

		# ニックネームを送信
		client_socket.sendall(nickname.encode('utf-8', errors='replace'))

		# 受信用のスレッドを作成
		receive_thread = threading.Thread(
			target=receive_message,
			args=(client_socket,),
			daemon=True
		)

		receive_thread.start()

		send_message(client_socket)

	except Exception as e:
		print(f'ERROR main: {e}')
	finally:
		try:
			client_socket.close()
		except:
			pass

if __name__ == '__main__':
	sys.exit(main())
