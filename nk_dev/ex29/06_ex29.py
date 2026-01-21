#!/usr/bin/env python3

import re
import sys
import html
import socket
import threading
from datetime import datetime

"""

	静的ファイルのHTTPリクエストに対してレスポンスをするローカルサーバー

	01-20:	md/static_file_guide.mdを読むところから

"""

client_count = 0
lock = threading.Lock()
routes = []

class Request:
	def __init__(self):
		self.method = None
		self.path = None
		self.version = None

class Response:
	def	__init__(self, status=200, reason='OK', headers=None, body=''):
		self.status = status
		self.reason = reason
		self.headers = headers if headers else {}
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
		response += self.body
		return response.encode('utf-8', errors='replace')

def	route(path):
	def	resister(handler):
		global routes

		pattern = re.sub(r'<(\w+)>', r'(?P<\1>[^/]+)', path)
		pattern = f'^{pattern}$'
		routes.append((re.compile(pattern), handler))
		return handler
	return resister

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
@route('/index.html')
def	handle_html():

	body = create_html(
		title='Welcome',
		h1='Welcome to My Server',
		content="""
		<p>このページのパスは '/' です</p>
		"""
	)
	return body

@route('/about')
def	handle_html():

	body = create_html(
		title='About',
		h1='About This Server',
		content="""
		<p>このサーバーはHTTPプロトコルの学習を目的としてpythonで作成されています</p>
		<ul>
			<li>TCPソケットによる通信</li>
			<li>threadingモジュールによる複数スレッドの処理</li>
			<li>HTTPリクエストに対するレスポンス</li>
		</ul>
		"""
	)
	return body

@route('/time')
def	handle_time():

	current_time = datetime.now().strftime('%Y-%m-%d %H-%M-%S')
	body = create_html(
		title='Current Time',
		h1='The Current Server Time',
		content=f"""
		<p style="font-size: 24px;">{current_time}</p>
		"""
	)
	return body

@route('/user/<user_id>')
def	handle_user(user_id):

	user_id = html.escape(user_id)
	body = create_html(
		title='User Page',
		h1=f'Welcome {user_id}',
		content=f"""
		<p>ようこそ {user_id} !</p>
		<p>このページはあなた専用のページです</p>
		"""
	)
	return body

@route('/posts/<post_id>')
def	handle_post(post_id):

	post_id = html.escape(post_id)
	body = create_html(
		title='Post Page',
		h1=f'Welcome to Post {post_id}',
		content=f"""
		<p>ポスト {post_id} へようこそ !</p>
		<p>このページは/post/{post_id}です</p>
		"""
	)
	return body

def handle_404():

	body = create_html(
		title='404 Not Found',
		h1='404 Not Found',
		content="""
		<p>そのパスは存在しません</p>
		"""
	)
	return body

def	parse_http(http_line, request_obj):
	parts = http_line.split()

	if len(parts) != 3:
		return False

	request_obj.method, request_obj.path, request_obj.version = parts
	return True

def	handle_client(client_socket):
	global client_count

	try:
		with lock:
			client_count += 1
			client_id = client_count
		print(f'handle_client: Connection detected id={client_id}')

		bytes_data = client_socket.recv(4096)

		if not bytes_data:
			print('Warning handle_client: Client disconnected', file=sys.stderr)
			return

		# リクエストを行ごとにパース
		request = bytes_data.decode('utf-8', errors='replace')
		request_line = request.split('\r\n')

		# parse_httpでリクエストオブジェクトに保存
		request_obj = Request()
		if not parse_http(request_line[0], request_obj):
			raise ValueError

		# ハンドラーの呼び出し
		response_obj = Response()
		matched = None
		for pattern, handler in routes:
			matched = pattern.match(request_obj.path)
			if matched:
				param = matched.groupdict()		# 正規表現に一致したタプルを取得
				response_obj.body = handler(**param)
				break							# マッチしたらbreakしてmatched変数の上書きを防ぐ

		# 適格なパスが存在しないなら404ハンドラーを呼ぶ
		if not matched:
			response_obj.status = 404
			response_obj.reason = 'Not Found'
			response_obj.body = handle_404()

		# ヘッダーにコンテンツサイズを追加
		content_length = f'{len(response_obj.body.encode('utf-8', errors='replace'))}'
		response_obj.headers['Content-Length'] = content_length

		# bytes列に変換して送信
		response_bytes = response_obj.to_bytes()
		client_socket.sendall(response_bytes)
	except ValueError as e:
		print(f'ERROR handle_client: {e}')

		# 500エラーを送信
		response = b'HTTP/1.1 500 Internal Server Error\r\n'
		response += b'Content-type: text/plain\r\n'
		response += b'Connection: close\r\n'
		response += b'\r\n'
		response += b'500 Internal Server Error\n'
		client_socket.sendall(response)
	finally:
		client_socket.close()

def	run_server(host='127.0.0.1', port=8080):
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	server_socket.bind((host,port))
	server_socket.listen(5)
	print(f'Server listening {host}:{port}')
	print('Resisted path:')
	for pattern, handler in routes:
		print(f'	{pattern.pattern} -> {handler.__name__}')
	print()

	try:
		while True:
			client_socket, client_address = server_socket.accept()

			client_thread = threading.Thread(
				target=handle_client,
				args=(client_socket, ),
				daemon=True
			)

			client_thread.start()
	except KeyboardInterrupt:
		print('\nServer closing')
	finally:
		server_socket.close()
		print('Server closed')

if __name__ == '__main__':
	run_server()
