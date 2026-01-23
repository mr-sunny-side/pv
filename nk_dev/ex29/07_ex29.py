#!/usr/bin/env python3

import re
import sys
import html
import socket
import threading

import mimetypes
from pathlib import Path

from urllib.parse import urlparse, parse_qs

"""
	ex29_06の復習
	01-22:	serve_static関数の記述 - 完了
			動的パスのルーティング - 完了
				- ハンドラーの記述 - 完了
				- デコレータの記述 - 完了

			handle_client関数：500エラーの送信記述		- 完了
			staticディレクトリにhtmlを格納				- time.html以外完了
			ルーティングによるHTMLファイルへのアクセス	- time.html以外完了

			クエリパラメータへの対応追加
				- Requestクラスの属性を追加
				- parse_http関数にクエリのパースを追加
				- /searchパスのハンドラーを追加
				- ハンドルクライアントの修正

			handle_client関数：エラー検出の具体化

"""

client_count = 0
routes = []
lock = threading.Lock()

STATIC_DIR = Path(__file__).parent / 'static'

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
			self.headers['COntent-Type'] = 'text/html; charset=utf-8'
		if 'Connection' not in self.headers:
			self.headers['Connection'] = 'close'

	def	to_bytes(self):

		response = f'HTTP/1.1 {self.status} {self.reason}\r\n'
		for label, detail in self.headers.items():
			response += f'{label}: {detail}\r\n'

		response += '\r\n'
		response_bytes = response.encode('utf-8', errors='replace')	#一旦ヘッダーまでエンコード
		# bodyのエンコード
		if isinstance(self.body, bytes):
			response_bytes += self.body
		else:
			response_bytes += self.body.encode('utf-8', errors='replace')

		return response_bytes

""" デコレータ """
def	route(path):
	def	register(handler):

		pattern = re.sub(r'<(\w+)>', r'(?P<\1>[^/]+)', path)
		pattern = f'^{pattern}$'
		routes.append((re.compile(pattern), handler))

		return handler
	return register

def	create_html(title, h1, content):

	html = f"""
	<!DOCTYPE html>
	<html lang="ja">
	<head>
		<meta charset="utf-8">
		<title>{title}</title>
	</head>
	<body>
		<h1>{h1}</h1>
		{content}
	</body>
	</html>
	"""

	return html

@route('/')
def	handle_html():

	file_path = STATIC_DIR / 'index.html'
	file_path = file_path.resolve()
	body = file_path.read_text(encoding='utf-8')

	return body

@route('/about')
def	handle_about():

	file_path = STATIC_DIR / 'about.html'
	file_path = file_path.resolve()
	body = file_path.read_text(encoding='utf-8')

	return body

@route('/search')
def	handle_search(request: Request):

	line = [
		'<!DOCTYPE html>',
		'<html lang="ja">',
		'<head>',
		'\t<meta charset="utf-8">',
		'\t<title>Search</title>',
		'</head>',
		'<body>',
		'\t<h1>Search Page</h1>',
		'\t<p>以下はリクエストされたクエリです</p>',
		'\t<ul>'
	]

	for label, detail in request.query.items():
		label = html.escape(label)
		detail = html.escape(' '.join(detail))		#detailはparse_qsメソッドでリストになっている
		line.append(f'\t\t<li>{label}: {detail}</li>')

	line.extend([
		'\t</ul>',
		'</body>',
		'</html>'
	])

	return '\n'.join(line)



@route('/user/<user_id>')
def	handle_user(user_id):

	user_id = html.escape(user_id)
	body = create_html(
		title='Welcome User',
		h1=f'Welcome {user_id} !',
		content=f'<p>このページは{user_id}専用ページです</p>'
	)

	return body

@route('/posts/<post_id>')
def	handle_post(post_id):

	post_id = html.escape(post_id)
	body = create_html(
		title='Welcome to Post Page',
		h1=f'Welcome to Post {post_id}',
		content=f'このページはポスト{post_id}の専用ページです'
	)

	return body

def	handle_404():

	body = create_html(
		title='404 Not Found',
		h1='404 Not Found',
		content='<p>そのパスは存在しません</p>'
	)

	return body

def	parse_http(http_line, request_obj):

	parts = http_line.split()
	if len(parts) != 3:
		return False

	request_obj.method = parts[0]
	request_obj.version = parts[2]

	url = urlparse(parts[1])
	request_obj.path = url.path
	request_obj.query_str = url.query
	request_obj.query = parse_qs(url.query)

	return True

def	serve_static(path):

	# パスを絶対パスに変換
	file_path = path.lstrip('/')
	file_path = STATIC_DIR / file_path
	file_path = file_path.resolve()

	# セキュリティチェック(ディレクトリトラバーサル対策)
	try:
		if not str(file_path).startswith(str(STATIC_DIR.resolve())):
			print(f'Warning serve_static: This path is invalid', file=sys.stderr)
			return None
	except Exception as e:
		print(f'Warning serve_static: {e}', file=sys.stderr)
		return None

	# ファイルパスの存在、ファイルかどうかの検証
	if not file_path.exists() or not file_path.is_file():
		print(f'serve_static: This path is not exist or dir', file=sys.stderr)
		return None

	# ファイルタイプの確認
	mime_type, _ = mimetypes.guess_type(str(file_path))
	if not mime_type:
		mime_type = 'application/octet-stream'

	# 適したリードメソッドを呼ぶ
	if mime_type.startswith('text/') or \
		mime_type in ['application/javascript', 'application/json']:
		# 静的ファイルはディスクにエンコードして保存されているので、読む形式を指定する
		body = file_path.read_text(encoding='utf-8')
		length = len(body.encode('utf-8', errors='replace'))
	else:
		body = file_path.read_bytes()
		length = len(body)

	return Response(
		status=200,
		reason='OK',
		headers={
			'Content-type': mime_type,
			'Content-Length': length
		},
		body=body
	)


def	handle_client(client_socket, client_address):
	"""
	適切なエラー検出を模索

	"""
	global client_count

	try:
		with lock:
			client_count += 1
			client_id = client_count
		print(f'handle_client: Connection detected id={client_id}', file=sys.stderr)
		print(f'	address: {client_address[0]}:{client_address[1]}')

		raw_data = client_socket.recv(4096)

		# リクエストデータが空なら終了
		if not raw_data:
			print('Warning handle_client: Request is empty', file=sys.stderr)
			return

		# リクエストをエンコードしてhttpリクエストを保存
		request_line = raw_data.decode('utf-8', errors='replace').split('\r\n')
		request_obj = Request()
		if not parse_http(request_line[0], request_obj):
			print(f'ERROR parse_http/handle_client: Cannot parse http request')
			raise ValueError

		# 静的ファイルのリクエストか検証
		static_obj = serve_static(request_obj.path)
		if static_obj:
			response_obj = static_obj
			response_bytes = response_obj.to_bytes()
			client_socket.sendall(response_bytes)
			return

		# 動的パスのハンドラー呼び出し
		response_obj = Response()
		for pattern, handler in routes:
			matched = pattern.match(request_obj.path)
			if matched:
				param = matched.groupdict()				# param == {user_id: 123}
				param['request'] = request_obj
				response_obj.body = handler(**param)	# **param == **{user_id: 123} == user_id=123
				break

		# 静的ファイルでなく、ハンドラーもいなかったら404として処理
		if not matched:
			response_obj.status = 404
			response_obj.reason = 'Not Found'
			response_obj.body = handle_404()
			response_bytes = response_obj.to_bytes()
			client_socket.sendall(response_bytes)
			return

		# コンテンツ長をヘッダーに保存し、送信
		response_obj.headers['Content-Length'] = len(response_obj.body.encode('utf-8', errors='replace'))
		response_bytes = response_obj.to_bytes()
		client_socket.sendall(response_bytes)
	except ValueError as e:
		print(e)
	except Exception as e:
		print(f'ERROR handle_client: {e}')

		response = b'HTTP/1.1 500 Internal Server Error\r\n'
		response += b'Content-Type: text/plane\r\n'
		response += b'Connection: close\r\n'
		response += b'\r\n'
		response += b'500 Internal Server Error\n'
		client_socket.sendall(response)
	finally:
		client_socket.close()


def	run_server(host='127.0.0.1', port=8080):
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	server_socket.bind((host, port))
	server_socket.listen(5)
	print(f'Server listening {host}:{port}', file=sys.stderr)
	print('Registered handler:')
	for pattern, handler in routes:
		print(f'	{pattern.pattern} -> {handler.__name__}')

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
		print('\nServer closing', file=sys.stderr)
	finally:
		server_socket.close()
		print('Server closed', file=sys.stderr)

if __name__ == '__main__':
	run_server()
