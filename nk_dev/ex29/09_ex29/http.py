import socket
import logging
from urllib.parse import urlparse, parse_qs

import config

config.setup_logging()

class Request:
	def	__init__(self):
		self.method = None
		self.path = None
		self.version = None
		self.length = None
		self.query = {}
		self.body = {}

def	parse_http(http_line: str, request_obj: Request) -> bool:
	parts = http_line.split()
	if len(parts) != 3:
		return False

	request_obj.method = parts[0]
	request_obj.version = parts[1]

	url = urlparse(parts[1])
	request_obj.path = url.path
	request_obj.query = parse_qs(url.query)

	return True


def	get_request(client_socket) -> int:
	## ヘッダー終了までバッファ
	buffer = b''
	while not b'\r\n\r\n' in buffer:
		buffer = client_socket.recv(config.BUFFER_SIZE)
		if buffer == b'':	# バッファが空ならループ終了
			break
		if config.MAX_READ < len(buffer):	# 見つからなければ終了
			logging.error('handle_client: Request header is too long')
			return -1

	# ヘッダーとボディを分割
	header_end = buffer.find(b'\r\n\r\n')	# ヘッダー終了文字のインデックスを捜索
	headers = buffer[:header_end]			# ヘッダー部分を保存
	body_part = buffer[header_end + 4:]			# ボディ部分を保存

	# ヘッダーをデコード
	headers = headers.decode('utf-8', errors='replace')

	# httpリクエストを分解
	request_obj = Request()
	header_line = headers.split('\r\n').strip()
	if not parse_http(header_line[0], request_obj):		# parse_httpでリクエスト最上部をパース
		logging.error('handle_client: Cannot parse http request')
		return -1

	# GETメッソドならここで終了
	if request_obj.method == 'GET':
		return 0

	## POSTメソッドの読み込み・保存
	# ボディ長を取得
	for header in header_line[1:]:
		header = header.split(':')
		if header[0].strip() == 'Content-Length':
			request_obj.length = int(header[1].strip())
			break

	# ボディ長が取得できなければエラー
	if request_obj.length is None:
		logging.error('handle_client: Cannot find Content-Length')
		return -1

	# 残りのボディ読み込み
	# ボディをデコードして保存
