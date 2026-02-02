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
	request_obj.version = parts[2]

	url = urlparse(parts[1])
	request_obj.path = url.path
	request_obj.query = parse_qs(url.query)

	return True

def	get_request(client_socket, request_obj) -> int:
	## ヘッダー終了までバッファ
	buffer = b''
	while not b'\r\n\r\n' in buffer:
		buffer += client_socket.recv(config.BUFFER_SIZE)
		if buffer == b'':	# バッファが空ならループ終了
			break
		if config.MAX_READ < len(buffer):	# 見つからなければ終了
			logging.error('get_request: Request header is too long')
			return
	logging.debug('get_request: found header end')

	# ヘッダーとボディを分割
	header_end = buffer.find(b'\r\n\r\n')	# ヘッダー終了文字のインデックスを捜索
	headers = buffer[:header_end]			# ヘッダー部分を保存
	body_part = buffer[header_end + 4:]			# ボディ部分を保存
	logging.debug('get_request: got raw header data')

	# ヘッダーをデコード
	headers = headers.decode('utf-8', errors='replace')
	logging.debug('get_request: decoded raw header data')

	# httpリクエストを分解
	header_line = headers.split('\r\n')
	if not parse_http(header_line[0], request_obj):		# parse_httpでリクエスト最上部をパース
		logging.error('get_request: Cannot parse http request')
		return -1
	logging.debug('get_request: got http request in header')

	# GETメッソドならここで終了
	if request_obj.method == 'GET':
		return 0
	logging.debug('get_request: request is GET method')

	## POSTメソッドの読み込み・保存
	# ボディ長を取得
	for header in header_line[1:]:
		header = header.split(':')
		if header[0].strip() == 'Content-Length':
			request_obj.length = int(header[1].strip())
			break
	logging.debug('get_request: found Content-Length in header')

	# ボディ長が取得できなければエラー
	if request_obj.length is None:
		logging.error('get_request: Cannot find Content-Length')
		return -1

	# 残りのボディ読み込み
	buffer = client_socket.recv(request_obj.length - len(body_part))
	body_part += buffer
	logging.debug('get_request: latest body_part is loaded')

	# ボディをデコード・パースして保存
	body_part = body_part.decode('utf-8', errors='replace')
	request_obj.body = parse_qs(body_part)
	return 0

def	print_request(request_obj):
	logging.info('===== Request Details =====')
	logging.info(f'{"method":<10}:{request_obj.method:>25}')
	logging.info(f'{"Path":<10}:{request_obj.path:>25}')
	logging.info(f'{"Version":<10}:{request_obj.version:>25}')
	logging.info('Query:')
	for label, detail in request_obj.query.items():
		detail = ','.join(detail)
		logging.info(f'\t{label}:{detail}')
	logging.info('Request Body:')
	for label, detail in request_obj.body.items():
		detail = ','.join(detail)
		logging.info(f'\t{label}:{detail}')
