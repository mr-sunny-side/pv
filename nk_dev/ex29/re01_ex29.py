#!/usr/bin/env python3

import threading
import socket

MAX_ATTEMPTS = 5

"""
	01-11: 備忘録を参照して構築
	 - conf_nickname関数とhandle_client関数を作成
	

	クライアントが接続したらリストを追加、
	 切断したらリストから削除するサーバー

"""

# グローバル変数
clients = {}  # {socket, nickname, address} の辞書のリスト
lock = threading.Lock()

class	ClientData:
	def __init__(self, nickname, client_socket, client_address):
		self.nickname = nickname
		self.client_socket = client_socket
		self.address = client_address

	def send_message(self, message):
		try:
			# messageがエンコードされてなかったらする
			message_bytes = message.encode('utf-8', errors='replace') if isinstance(message, str) else message
			self.client_socket.sendall(message_bytes)	# メッセージを送信
			return True
		except Exception as e:
			print(f'ERROR send_message/ClientData: Cannot send message')
			print(f'Exception: {e}')
			return False


def	create_server_socket(host='127.0.0.1', port=8080):
	"""
	1. ソケットの作成
	2. 再起動時にTCP通信がポートを専有しないように設定
	3. ソケットにIPアドレスとポート番号を紐付け
	4. 接続待ち状態にして接続キューを指定

	"""

	# ソケット作成
	# AF_INET == IPv4
	# SOCK_STEAM == TCP
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	# 再起動時にアドレスの再利用を許可
	# ソケットの設定を指定　SOL_SOCKET
	# アドレスの再利用　SO_REUSEADDR
	server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

	# IPアドレスとポートの紐付け(bind)
	server_socket.bind((host, port))

	# 接続待ち状態に。一度の接続要求は5まで
	server_socket.listen(5)

	return server_socket

# 不正なニックネームを検出
def	conf_nickname(nickname):
	# 不正なニックネームを検出
	if not nickname or len(nickname) > 20:
		return -1

	# すでに使われているニックネームを検出
	with lock:
		if nickname in clients:
			return -1
	return 0


def	broadcast(message):
	# messageがstr確認・必要ならエンコード
	if isinstance(message, str):
		message_bytes = message.encode('utf-8', errors='replace')

	# 全員に対して送信ループ
	for user in clients.keys():
		# send_massege関数が失敗したら終了
		if not clients[user].send_message(message_bytes):
			print('ERROR send_massege/sendall: return False')
			return False
	return True

def	handle_client(client_socket, client_address):
	"""
	個別クライアントの処理

	# ニックネームを受信
	# クライアントリストに追加
	# 参加通知を全員に送信

	"""
	nickname = None
	valid_nickname = False
	
	try:
		# 適格なニックネームが入力されるまでループ
		for attempt in range(MAX_ATTEMPTS):
			# ニックネームを受信
			nickname_bytes = client_socket.recv(1024)
			
			# 切断チェック
			if not nickname_bytes:
				print(f'Client disconnected during nickname input {client_address[0]}:{client_address[1]}')
				return		# 関数を抜ける
			
			# ニックネームをデコード
			nickname = nickname_bytes.decode('utf-8', errors='replace').strip()
			
			# 不正・重複したニックネームを検出、再入力を促す
			if conf_nickname(nickname) == -1:
				error_message = '/ ERROR: This nickname is Invalid or already used'
				error_message += f'Your input: {nickname}'
				client_socket.sendall(error_message.encode('utf-8', errors='replace'))
				continue
			
			# エラー検証に引っかからなければ入力ループ終了
			valid_nickname = True	# 適格なニックネームのフラグ
			break

		# 適格なニックネームを得てループを抜けたか検証
		if not valid_nickname:
			client_socket.sendall(b'/ ERROR: Too many attempt')
			client_socket.sendall(b'Disconnecting...')
			return
		
		# ユーザーを辞書に追加・ニックネーム入力ループを終了
		with lock:
			clients[nickname] = ClientData(nickname, client_socket, client_address)

		# ログインを全員に通知
		login_message = f'/ Hello {nickname}!'
		if not broadcast(login_message):
			client_socket.sendall(b'/ Warning: Cannot send login_message')
			print('Warning: broadcast/handle_client: Cannot send login message')
			print(f'Nickname: {nickname}')
			print(f'Address: {client_address[0]}:{client_address[1]}')

		# ユーザーが切断するまで接続を継続・メッセージをユーザーにブロードキャスト
		while True:
			message_bytes = client_socket.recv(1024)
			
			# 切断チェック
			if not message_bytes:
				print(f'{nickname} disconnected')
				return
			
			message = message_bytes.decode('utf-8', errors='replace')
			
			# メッセージが空なら無視
			if not message:
				continue
			
			# チャットとしてブロードキャスト
			chat_message = f'{nickname}: {message}'
			if not broadcast(chat_message):
				client_socket.sendall(b'/ Warning: Cannot send chat message')
				print('Warning broadcast/handle_client: Cannot send chat message')
				print(f'Nickname: {nickname}')
				print(f'Address: {client_address[0]}:{client_address[1]}')
				
	finally:
		if nickname and nickname in clients:	# クライアント辞書削除の防衛
			logout_message = f'/ {nickname} logout'	# 先にログアウトメッセージを送信
			if broadcast(logout_message)
				print('Warning broadcast/handle_client: Cannot send logout message')
				print(f'Nickname: {nickname}')
				print(f'Address: {client_address[0]}:{client_address[1]}')
			with lock:				# 排他制御
				del clients[nickname]	# クライアント辞書から削除

		# クライアントソケットを閉じる
		client_socket.close()

def	run_server(host='127.0.0.1', port=8080):
	"""
	サーバーのメインループ

	"""

	# ソケットの作成
	server_socket = create_server_socket(host, port)
	print(f'server_listening: {host}:{port}')
	print('Press Ctrl + C to stop')

	try:
		while True:
			# サーバーを待機状態にする
			client_socket, client_address = server_socket.accept()
			

			# スレッド作成
			# Threadは大文字
			client_thread = threading.Thread(
				target=handle_client,
				args=(client_socket, client_address),
				daemon=True
			)

			client_thread.start()


	except KeyboardInterrupt:
		print('Shutting down server...')
	finally:
		server_socket.close()
		print('Servser stopped')

if __name__ == "__main__":
	run_server()

