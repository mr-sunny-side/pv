#!/usr/bin/env python3

import sys
import threading
import socket
import re
import html
from datetime import datetime

"""
	デコレータを使って任意のユーザーidパスに適したhtmlを返すサーバー


"""
client_count = 0
lock = threading.Lock()
routes = []

class Request:
	def	__init__(self):
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
			response += f'{label}: {detail}'

		response += '\r\n'
		response += self.body

		return response.encode('utf-8', errors='replace')

def	parse_http(http_line, request_obj):
	parts = http_line.split()

	if len(parts) != 3:
		return False

	request_obj.method, request_obj.path, request_obj.version = parts
	return True

# ユーザーIDの正規表現を構築し、ルーとリストに保存するデコレータ
def	route(path_case):	# path_case == /user/<user_id>
	def	decorator(handler):
		# re.sub == 置換
		# ?P == マッチに名前を付けてタプルとして保存
		# () == 部分を捕捉
		pattern = re.sub(r'<(\w+)>', r'(?P<\1>[^/]+)', path_case)	# <user_id>の部分を正規表現のマッチングパターンに変換
		pattern = f'^{pattern}$'
		routes.append((re.compile(pattern), handler))

		return handler
	return decorator

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
		<p>このサーバーはHTTPプロトコルの学習を目的としてpythonで作成されました</p>
		<p>以下のようなパスにアクセスしてみてください</p>
		<ul>
			<li>/index.html</li>
			<li>/about</li>
			<li>/time</li>
			<li>/user/<alphabet></li>
			<li>/post/<alphabet></li>
		</ul>
		"""
	)

	return body

@route('/about')
def	handle_about():

	body = create_html(
		title='About',
		h1='About This Server',
		content="""
		<p>このサーバーはHTTPプロトコルの学習を目的としてpythonで作成されました</p>
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
		<p>現在のサーバー時間を表示します</p>
		<p style="font-size: 24px;">{current_time}</p>
		"""
	)

	return body

@route('/user/<user_id>')
def	handle_user(user_id):

	user_id = html.escape(user_id)	# スクリプト攻撃への対策
	body = create_html(
		title='Welcome User',
		h1=f'Welcome {user_id}',
		content=f"""
		<p>ようこそ {user_id} !</p>
		<p>このページはユーザー専用ページです</p>
		"""
	)

	return body

@route('/posts/<post_id>')
def	handle_post(post_id):

	user_id = html.escape(post_id)	# スクリプト攻撃への対策
	body = create_html(
		title='Post',
		h1=f'Post {post_id}',
		content=f"""
		<p>投稿ページへようこそ !</p>
		<p>このページのパスは/posts/{post_id}です</p>
		"""
	)

	return body


def	handle_client(client_socket):
	global client_count

	try:
		# クライアントIDを付与
		with lock:
			client_count += 1
			client_id = client_count

		print(f'handle_client: Connection detected id=[{client_id}]')

		# リクエストが空文字なら切断とみなし終了
		request_bytes = client_socket.recv(4096)
		if not request_bytes:
			print(f'Warning id={client_id}/handle_client: Client disconnected', file=sys.stderr)
			return

		# デコードしたリクエストが空文字なら終了
		request = request_bytes.decode('utf-8', errors='replace')
		if not request:
			print(f'Warning id={client_id}/handle_client: Request is empty', file=sys.stderr)
			return

		# リクエストのメソッドなどをオブジェクトに格納、失敗は終了
		request_obj = Request()
		request_line = request.split('\r\n')
		if not parse_http(request_line[0], request_obj):
			raise ValueError

		# ルートからハンドラーを探し、htmlをオブジェクトに保存
		response_obj = Response()
		for pattern, handler in routes:
			matched = pattern.match(request_obj.path)
			if matched:
				param = matched.groupdict()						# 正規表現に一致したタプルを取得
				response_obj.body = handler(**param)			#**をつけることで、中身を展開している。空なら空で渡す

		# ヘッダーにコンテンツサイズを保存
		content_length = f'{len(response_obj.body.encode('utf-8', errors='replace'))}'
		response_obj.headers['Content-Length'] = content_length

		# エンコードして送信
		response_bytes = response_obj.to_bytes()
		client_socket.sendall(response_bytes)
	except ValueError as e:
		print(f'ERROR handle_client: {e}')

		response = b'HTTP/1.1 500 Internal Server Error\r\n'
		response += b'Content-Type: text/plain\r\n'
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
	print(f'run_server: Server listening {host}:{port}')
	print()
	print('Resisted Routes:')
	for pattern, handler in routes:
		print(f'	{pattern.pattern} -> {handler.__name__}')



	try:
		while True:
			client_socket, client_address = server_socket.accept()

			# スレッドの起動
			client_thread = threading.Thread(
				target=handle_client,
				args=(client_socket, ),
				daemon=True
			)
			client_thread.start()
	except KeyboardInterrupt:
		print('Server closing...')
	finally:
		server_socket.close()
		print('server closed')

if __name__ == '__main__':
	run_server()
