#!/usr/bin/env	python3

"""
	01-13: handle_client関数の第二段階まで記述
		第三段階から
"""

import sys
import socket
import threading

MAX_ATTEMPT = 5

clients = {}
lock = threading.lock()

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
	server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR)

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
	if attempt > MAX_ATTEMPT:
		message = 'ERROR: Too many attempt\n'
		message += 'Disconnecting...\n'
		client_socket.sendall(message.encode('utf-8', errors='replace'))
		return None

	return nickname





def	handle_client(client_socket, client_address):
	global	clients

	try:
		nickname = process_nickname(client_socket)

		# ニックネーム作成ができなかった場合終了
		if not nickname:
			return

		# 排他制御下でclientオブジェクトを作成
		with lock:
			clients[nickname] = ClientData(nickname, client_socket, client_address)

		# ログインメッセージをブロードキャスト、失敗時は終了
		login_message = f'Say hello to {nickname} !\n'
		if not broadcast(login_message):
			return
