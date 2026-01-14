#!/usr/bin/env python3

"""

"""

import sys
import socket
import threading

MAX_ATTEMPT = 5
# スレッド間のシステム終了フラグ
shutdown_flag = threading.Event()

clients = {}
lock = threading.Lock()

class ClientData:
	# ニックネーム、ソケット、アドレスを保存
	def	__init__(self, nickname, client_socket, client_address):
		self.nickname = nickname
		self.client_socket = client_socket
		self.address = client_address

	# ユーザーにメッセージを送信
	def	send_message(self, message) -> bool:
		try:
			# メッセージがstrだったらエンコード
			if isinstance(message, str):
				message = message.encode('utf-8', errors='replace')
			# エンコード済みのメッセージをユーザーに送信
			self.client_socket.sendall(message)
			return True
		except Exception as e:
			print(f'ERROR send_message/ClientData: {e}')
			return False

def	create_server_socket(host='127.0.0.1', port=8080):

	# IPv4, TCPでソケットを作成
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	# 再起動時にアドレスの再利用を許可
	server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

	# IPアドレスとポートを紐付ける
	server_socket.bind((host, port))

	# 接続待ち状態にし、一度に5つの接続要求に対応
	server_socket.listen(5)

	return server_socket

def	conf_nickname(nickname: str) -> int:
	global	clients

	# 空文字、20文字以内の確認
	if not nickname or 20 < len(nickname):
		return -1
	# 排他制御下で重複を確認
	with lock:
		if nickname in clients:
			return 1
	return 0

# 全ユーザーにメッセージを送信する関数
def	broadcast(message) -> bool:
	global	clients

	# str型ならエンコード
	if isinstance(message, str):
		message = message.encode('utf-8', errors='replace')
	try:
		# 全ユーザーソケットへ送信ループ
		for user in clients.keys():
			clients[user].send_message(message)
		return True
	except Exception as e:
		print(f'ERROR broadcast: {e}')
		return False

# ニックネーム受信のプロセス関数
def	process_nickname(client_socket) -> str | None:
	# マクロ回数までニックネームを受付
	for attempt in range(MAX_ATTEMPT):
		nickname_bytes = client_socket.recv(1024)

		# 空文字なら切断として終了
		if not nickname_bytes:
			print('Client disconnected')
			return None

		# デコード, strip()
		nickname = nickname_bytes.decode('utf-8', errors='replace').strip()

		# conf_nicknameの結果を保存
		result = conf_nickname(nickname)

		# ニックネームが空文字・20文字以上なら次のループ
		if result == -1:
			message = f'Warning: Nickname "{nickname}" is invalid\n'
			client_socket.sendall(message.encode('utf-8', errors='replace'))
			continue
		# ニックネームが重複なら次のループ
		elif result == 1:
			message = f'Warning: Nickname "{nickname}" is already used\n'
			client_socket.sendall(message.encode('utf-8', errors='replace'))
			continue
		# 適格なニックネームならループ終了
		elif result == 0:
			message = f'Hello {nickname} !\n'
			client_socket.sendall(message.encode('utf-8', errors='replace'))
			break

	# 試行回数を超過したら終了
	# rangeはインデックスで数えているので注意
	if attempt >= MAX_ATTEMPT - 1:
		message = 'ERROR: Too many attempt\n'
		message += 'Disconnecting...\n'
		client_socket.sendall(message.encode('utf-8', errors='replace'))
		return None

	return nickname

# メッセージ受信プロセス関数
# 切断・エラー時はFalse、次のループへ行くならTrue
def	receive_message(nickname, client_socket) -> bool:
	message_bytes = client_socket.recv(1024)

	# バイト列が空なら切断と判断
	if not message_bytes:
		return False

	# メッセージをデコード・空文字なら次のループへ
	message = message_bytes.decode('utf-8', errors='replace').strip()
	if not message:
		return True

	# メッセージをブロードキャスト
	message = f'{nickname}: {message}\n'
	if not broadcast(message):
		return False

	return True

def	handle_client(client_socket, client_address):
	global	clients

	try:
		# 1. 適格なニックネームの確認・ニックネーム作成ができなかった場合終了
		nickname = process_nickname(client_socket)
		if not nickname:
			return

		# 2. 排他制御下でclientオブジェクトを作成
		with lock:
			clients[nickname] = ClientData(nickname, client_socket, client_address)

		# ログインメッセージをブロードキャスト、失敗時は終了
		login_message = f'Say hello to {nickname} !\n'
		if not broadcast(login_message):
			return

		# 3. メッセージ受信ループ
		while True:
			# クライアント切断・ブロードキャスト失敗時は終了
			if not receive_message(nickname, client_socket):
				return
			# 問題がなければ受信待ちへ戻る
			else:
				continue

	except Exception as e:
		print(f'ERROR handle_client: {e}')
		return
	finally:
		# クライアント辞書に存在を確認し、排他制御下でクライアントデータを削除
		if nickname in clients:
			with lock:
				del clients[nickname]
				print(f'{nickname} logout')

				message = f'{nickname} logout\n'
				broadcast(message)

		# クライアントソケットを閉じる
		try:
			client_socket.close()
		except:
			pass

# サーバーのメイン関数
def	run_server(host='127.0.0.1', port=8080):

	# ソケットを作成
	server_socket = create_server_socket(host, port)
	print(f'Server listening {host}:{port}')
	print('Press Ctrl + C to stop')
	print()

	try:
		# 接続待ちループ
		while True:
			# クライアントに接続
			client_socket, client_address = server_socket.accept()
			print(f'run_server: client detected {client_address[0]}:{client_address[1]}')

			client_thread = threading.Thread(
				target=handle_client,
				args=(client_socket, client_address),
				daemon=True
			)

			client_thread.start()

	except KeyboardInterrupt:
		print('run_server: shuting down server')
	finally:
		try:
			server_socket.close()
		except:
			pass
		print('Server stopped')

if __name__ == '__main__':
	run_server()
