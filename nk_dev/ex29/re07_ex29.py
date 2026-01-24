#!/usr/bin/env python3

import re
import sys
import html
import socket
import threading

from urllib.parse import urlparse, parse_qs
from pathlib import Path
import mimetypes

STATIC_DIR = Path(__file__).parent / 'static'

client_count = 0
lock = threading.Lock()
routes = []

"""
	01-24:	serve_static関数の記述	- 完了
			to_bytesメソッドの記述	- 完了
			動的パスのルーティング	- time.html意外完了
				- ハンドラーの記述	- 上に同じ
				- デコレータの記述	- 完了

			クエリパラメータへの対応追加				- 完了
				- Requestクラスの属性を追加				- 完了
				- parse_http関数にクエリのパースを追加	- 完了
				- /searchパスのハンドラーを追加			- 完了
				- ハンドルクライアントの記述			- 完了

			ValueErrorで出力されるロジックエラーの修正


"""
class Request:
	def	__init__(self):

		self.method = None
		self.path = None
		self.version = None
		self.query_str = None
		self.query = {}

class Response:
	def	__init__(self, status=200, reason='OK', headers={}, body=''):

		self.status = status
		self.reason = reason
		self.headers = headers
		self.body = body

		if 'Content-Type' not in self.headers:
			self.headers['Content-Type'] = 'text/html; charset=utf-8'
		if 'Connection' not in self.headers:
			self.headers['Connection'] = 'close'

	def	to_bytes(self):

		response = f'HTTP/1.1 {self.status} {self.reason}\r\n'
		for label, detail in self.headers.items():
			response += f'{label}: {detail}\r\n'

		response += '\r\n'
		response = response.encode('utf-8', errors='replace')
		if isinstance(self.body, bytes):
			response += self.body
		else:
			response += self.body.encode('utf-8', errors='replace')

		return response

def	route(path):
	def	register(handler):

		global routes
		pattern = re.sub(r'<(\w+)>', r'(?P<\1>[^/]+)', path)
		pattern = f'^{pattern}$'
		routes.append((re.compile(pattern), handler))
		return handler
	return register

def	create_html(title, h1, content):

	lines = [
		'<!DOCTYPE html>',
		'<html lang="ja">',
		'<head>',
		'\t<meta charset="utf-8">',
		f'\t<title>{title}</title>',
		'</head>',
		'<body>',
		f'\t<h1>{h1}</h1>',
		content,
		'</body>',
		'</html>'
	]

	return '\n'.join(lines)

@route('/')
def	handle_html():
	file_path = STATIC_DIR / 'index.html'
	body = file_path.read_text(encoding='utf-8')
	length = len(body.encode('utf-8', errors='replace'))

	return Response(
		status=200,
		reason='OK',
		headers={
			'Content-Type': 'text/html; charset=utf-8',
			'COntent-Length': length
		},
		body=body
	)

@route('/about')
def	handle_about():
	file_path = STATIC_DIR / 'about.html'
	body = file_path.read_text(encoding='utf-8')
	length = len(body.encode('utf-8', errors='replace'))

	return Response(
		status=200,
		reason='OK',
		headers={
			'Content-Type': 'text/html; charset=utf-8',
			'Content-Length': length
		},
		body=body
	)

@route('/user/<user_id>')
def	handle_user(user_id):

	user_id = html.escape(user_id)
	content = f'\t<p>ようこそ {user_id} !</p>\n'
	content += f'\t<p>このページはユーザー専用のダミーページです</p>\n'
	body = create_html(
		title='Welcome User',
		h1=f'Welcome {user_id}',
		content=content
	)
	length = len(body.encode('utf-8',errors='replace'))

	return Response(
		status=200,
		reason='OK',
		headers={
			'Content-Type': 'text/html; charset=utf-8',
			'Content-Length': length
		},
		body=body
	)

@route('/search')
def	handle_search(request_obj: Request):

	content = '\t<p>このページは検索ページのダーミーページです</p>\n'
	content += '\t<p><以下はあなたが入力したクエリです</p>\n'
	content += '\t<ul>\n'
	# クエリをhtmlのリストとして書き込むループ
	for label, detail in request_obj.query.items():
		label = html.escape(label)
		detail = ''.join(detail)						# クエリは同種複数の場合リストで保管されているので、まず連結する
		detail = html.escape(detail)
		content += f'\t\t<li>{label}: {detail}</li>\n'
	content += '\t</ul>\n'

	body = create_html(
		title='Search Page',
		h1='Search Page',
		content=content
	)
	length = len(body.encode('utf-8', errors='replace'))

	return Response(
		status=200,
		reason='OK',
		headers={
			'Content-Type': 'text/html; charset=utf-8',
			'Content-Length': length
		},
		body=body
	)

def	static_search(path) -> Response | None:

	file_path = path.lstrip()
	file_path = STATIC_DIR / file_path
	file_path.resolve()

	# staticディレクトリ下かチェック
	try:
		if not str(file_path).startswith(str(STATIC_DIR.resolve())):
			print('Warning static_search: Invalid path')
			return None
	except Exception as e:
		print('ERROR Exception static_search: Invalid path')
		print(f'\t{e}')
		return None

	# ファイルが存在するか、ファイルかどうかチェック
	if not file_path.exists() or not file_path.is_file():
		print('static_search: This path is not exist or not file')
		return None

	# ファイル形式の判定
	mime_types, _ = mimetypes.guess_type(file_path)
	if not mime_types:
		mime_types = 'application/octet-stream'

	# 適格な読み込み関数で読み込み
	if mime_types.startswith('text/') or mime_types in ['application/javascript', 'application/json']:
		body = file_path.read_text(encoding='utf-8')
		length = len(body.encode('utf-8', errors='replace'))
	else:
		body = file_path.read_bytes()
		length = len(body)

	return Response(
		status=200,
		reason='OK',
		headers={
			'Content-Type': mime_types,
			'Content-Length': length
		},
		body=body
	)

def parse_http(http_line, request_obj: Request):

	parts = http_line.split()
	if not len(parts) != 3:
		return False

	request_obj.method = parts[0]
	request_obj.version = parts[2]

	# リクエストパスの分解、クエリの保存
	url = urlparse(parts[1])
	request_obj.path = url.path
	request_obj.query_str = url.query
	request_obj.query = parse_qs(url.query)
	return True


def	handle_client(client_socket, client_address):

	global routes
	global client_count
	try:
		# クライアントに接続順でidを付与
		with lock:
			client_count += 1
			client_id = client_count
		print(f'handle_client: Connection detected')
		print(f'\t{client_address[0]}:{client_address[1]} id={client_id}')
		# リクエストデータの有無確認
		raw_data = client_socket.recv(4096)
		if not raw_data:
			print('Warning handle_client: request if empty', file=sys.stderr)
			return

		decoded_data = raw_data.decode('utf-8', errors='replace')
		if not decoded_data.strip():
			return

		# リクエストデータを分解
		request_line = decoded_data.split('\r\n')
		request_obj = Request()
		if not parse_http(request_line[0], request_obj):
			raise ValueError

		# staticディレクトリから静的ファイルの捜索
		static_data = static_search(request_obj.path)
		if static_data:
			response_obj = static_data
			response_bytes = response_obj.to_bytes()
			client_socket.sendall(response_bytes)
			return

		# 基本htmlとパスのルーティング
		# /, /about, /time, /search
		for pattern, handler in routes:
			matched = pattern.match(request_obj.path)
			param = matched.groupdict()
			param['request_obj'] = request_obj
			response_obj = handler(**param)

		response_bytes = response_obj.to_bytes()
		client_socket.sendall(response_bytes)
	except ValueError as e:
		print(f'ValueError handle_client: {e}')
		return
	finally:
		client_socket.close()

def	run_server(host='127.0.0.1', port=8080):
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	server_socket.bind((host, port))
	server_socket.listen(5)
	print(f'Server listening {host}:{port}')
	# ルートの表示

	try:
		while True:

			client_socket, client_address = server_socket.accept()

			client_thread = threading.Thread(
				target=handle_client,
				args=(client_socket, client_address),
				daemon=True
			)

			client_thread.start()
	except KeyboardInterrupt:
		print('\nServer closing')
	finally:
		server_socket.close()
		print('Server Closed')


if __name__ == '__main__':
	run_server()
