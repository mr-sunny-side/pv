#!/usr/bin/env python3

import sys
import threading
import socket
from datetime import datetime

"""
	デコレータ関数を自作してルートごとにHTTPリクエストを返すサーバー

	01-18: まずは各ハンドラー関数とcreate_html関数の作成


"""
client_count = 0
lock = threading.Lock()
handler_dict = {}

class Request:
	def	__init__(self):
		self.method = None
		self.path = None
		self.version = None

class Response:
	def	__init__(self, status=200, reason='OK', headers=None, body=''):
		self.status = status
		self.reason = reason
		self.headers = headers if headers else {}	# headerが空だった場合、辞書だけ作成
		self.body = body

		# headersが空でも最低限の情報を追加
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

def	handle_index():

	body = create_html(
		title='Welcome',
		h1='Welcome to My Server',
		content="""
		<p>このサーバーはHTTPプロトコルを学ぶために、pythonで作成されています。</p>
		<p>次のようなパスでHTTPリクエストを送ってみてください !</p>
		<ul>
			<li>/index.html</li>
			<li>/about</li>
			<li>/time</li>
			<li>/noexist</li>
		</ul>
		"""
	)

	return body

def	handle_about():

	body = create_html(
		title='About',
		h1='About This Server',
		content="""
		<p>このサーバーはHTTPプロトコルを学ぶために、pythonで作成されています。</p>
		<ul>
			<li>TCPソケットによる通信</li>
			<li>HTTPプロトコルによるレスポンス</li>
			<li>threadingモジュールによる複数スレッドの処理</li>
		</ul>
		"""
	)

	return body

def	handle_time():

	current_time = datetime.now().strftime('%Y-%m-%d %H-%M-%S')

	body = create_html(
		title='Current time',
		h1='The Current Server Time',
		content=f"""
		<p>現在のサーバー時間を表示します</p>
		<p style="font-size: 24px;">{current_time}</p>
		"""
	)

	return body

def	handle_404():

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

# デコレータ
def	route(path):
	def	resister(handler):
		global handler_dict

		handler_dict[path] = handler
		return handler
	return resister

def	handle_client(client_socket):
	global client_count

	try:
		# 排他制御下でクライアントスレッドにIDを付与
		with lock:
			client_count += 1
			client_id = client_count

		print(f'Client_ID[{client_id}] Connected')

		data = client_socket.recv(4096)

		# 空文字が送られてきたら終了
		if not data:
			return

		# デコードして行ごとにパース・リクエストオブジェクトを作成
		request = data.decode('utf-8', errors='replace')
		request_lines = request.split('\r\n')
		request_obj = Request()

		# httpリクエストをパースできなかったら終了
		if not parse_http(request_lines[0], request_obj):
			raise ValueError

		# レスポンスオブジェクトを作成
		response_obj = Response()
		# パスに応じたハンドラーを呼び出し、オブジェクトにhtmlを保存
		handler = handler_dict.get(request_obj.path)
		if handler:
			response_obj.body = handler()
		else:
			response_obj.body = handle_404()
			response_obj.status = 404
			response_obj.reason = '404 Not Found'

		# レスポンスのコンテンツサイズのヘッダーを作成
		content_length = f'{len(response_obj.body.encode('utf-8', errors='replace'))}'
		response_obj.headers['Content-Length'] = content_length

		# 完成したレスポンスをエンコード
		response_bytes = response_obj.to_bytes()

		client_socket.sendall(response_bytes)


	except ValueError as e:
		print(f'ERROR handle_client: {e}')

		error_response = b'HTTP/1.1 500 Internal Server Error\r\n'
		error_response += b'Content-Type: text/plain\r\n'
		error_response += b'Connection: close'
		error_response += b'\r\n'
		error_response += b'500 Internal Server Error\n'

		client_socket.sendall(error_response)
	finally:
		client_socket.close()


def	run_server(host='127.0.0.1', port=8080):
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	server_socket.bind((host, port))
	server_socket.listen(5)
	print(f'Server listening {host}:{port}')

	# ハンドラーを登録
	route('/')(handle_index)
	route('/index.html')(handle_index)
	route('/about')(handle_about)
	route('/time')(handle_time)

	try:
		while True:
			client_socket, client_address = server_socket.accept()
			print('run_server: Connection detected')

			client_thread = threading.Thread(
				target=handle_client,
				args=(client_socket, ),
				daemon=True
			)

			client_thread.start()
	except KeyboardInterrupt:
		print('\nServer closing...')
	finally:
		server_socket.close()
		print('Server closed')

if __name__ == '__main__':
	run_server()
