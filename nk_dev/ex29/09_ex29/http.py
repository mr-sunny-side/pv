import logging
import socket

import config

config.setup_logging()

class Request:
	def	__init__(self):
		self.method = None
		self.path = None
		self.version = None
		self.query = {}
		self.body = {}

def	get_request(client_socket):
	# ヘッダー終了までバッファ
	buffer = b''
	while b'\r\n\r\n' in buffer:
		buffer = client_socket.recv(config.BUFFER_SIZE)
		if buffer == b'':	# バッファが空ならループ終了
			break
		if config.MAX_READ < len(buffer):	# 見つからなければ終了
			logging.error('handle_client: Request header is too long')
			raise ValueError

	# ヘッダーとボディを分割
	header_end = buffer.find(b'\r\n\r\n')	# ヘッダー終了文字のインデックスを捜索
	headers = buffer[:header_end]			# ヘッダー部分を保存
	body_part = buffer[header_end:]			# ボディ部分を保存

	# リクエストを分解
	header_line = headers.split('\r\n').strip()
	# parse_httpでリクエスト最上部をパース
