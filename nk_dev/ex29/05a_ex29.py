#!/usr/bin/env python3

import sys
import threading
import socket
from datetime import datetime

"""
	辞書を使ったルーティングを行い、リクエストパスに対して適切なhtmlを返すサーバー

	01-17:	各ハンドラー関数(404含む)と、create_html関数の作成 - 完了
			レスポンスクラスと、バイト列の完成形として返す内部関数の作成 - 完了
				※ レスポンスオブジェクトは独立したスレッド下で作成、使用される



			- create_html関数が完了、各ハンドラーを作成中
"""

client_count = 0
lock = threading.Lock()

# リクエストを保存しておくクラス
class Request:
	def	__init__(self):
		self.method = None
		self.path = None
		self.version = None

# レスポンスを保存し、必要に応じてバイト列のHTTPプロトコルとして返すクラス
class Response:
	def	__init__(self, status=200, reason='OK', headers=None, body=''):
		self.status = status
		self.reason = reason
		self.headers = headers if headers else {}	# ヘッダーは辞書として保存
		self.body = body

		# 未定義でも最低限のヘッダーは用意する
		if 'Content-Type' not in self.headers:
			self.headers['Content-Type'] = 'text/html; charset=utf-8'
		if 'Connection' not in self.headers:
			self.headers['Connection'] = 'close'

	# バイトにしてレスポンスとして整える
	def	to_bytes(self):
		response = f'HTTP/1.1 {self.status} {self.reason}\r\n'

		# ヘッダーをループで保存
		for label, detail in self.headers.items():
			response += f'{label}: {detail}\r\n'

		response += '\r\n'
		response += self.body

		return response.encode('utf-8', errors='replace')

# htmlのガワを作る
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
		<p>このサーバーはHTTPレスポンスをするサーバーの学習を目的として、pythonで書かれています</p>
		<p>次のようなパスにアクセスしてみてください！</p>
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
		<p>このサーバーはHTTPリクエストをするサーバーの学習を目的として、pythonで書かれています。</p>
		<ul>
			<li>TCPソケットによる通信</li>
			<li>threadingモジュールによる複数スレッドの処理</li>
			<li>HTTPプロトコルによるレスポンス</li>
		</ul>
		"""
	)

	return body

def	handle_time():

	current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

	body = create_html(
		title='Current Time',
		h1='The Server Current Time',
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
		content='<p>そのパスは存在しません</p>'
	)

	return body

# ルートを保存
routes = {
	'/': handle_index,
	'/index.html': handle_index,
	'/about': handle_about,
	'/time': handle_time
}

def	parse_http(http_line, request_data):
	parts = http_line.split()

	if len(parts) != 3:
		return False

	request_data.method, request_data.path, request_data.version = parts
	return True

def	handle_client(client_socket):
	global client_count

	try:

		with lock:
			client_count += 1
			client_id = client_count
			print(f'Client [{client_id}] connected')

		raw_request = client_socket.recv(4096)

		# リクエストが空（通信切断）なら終了
		if not raw_request:
			return

		# リクエストをデコード・行ごとにパース
		decoded_request = raw_request.decode('utf-8', errors='replace')
		parsed_request = decoded_request.split('\r\n')

		# httpリクエストをリクエストオブジェクトに保存
		request_data = Request()
		if not parse_http(parsed_request[0], request_data):
			print('ERROR parse_http/handle_client: returned error')
			return

		body = None			# ハンドラーにhtmlを入れてもらう変数
		# ハンドラーの呼び出し
		for path, handler in routes.items():
			if path == request_data.path:
				body = handler()

		# 一致するパスがなければ404htmlを格納
		if not body:
			body = handle_404()

		headers = {}		# レスポンスオブジェクトに保存するヘッダー辞書
		# ヘッダーの作成・レスポンスオブジェクトに保存
		headers['Content-Type'] = 'text/html; charset=utf-8'
		headers['Content-Length'] = f'{len(body.encode("utf-8",errors="replace"))}'
		response_data = Response(headers=headers, body=body)

		response = response_data.to_bytes()

		client_socket.sendall(response)

	except Exception as e:
		response = b'HTTP/1.1 500 Internal Server Error\r\n'
		response += b'Content-Type: text/plain\r\n'
		response += b'Connection: close\r\n'
		response += b'\r\n'
		response += b'500 Internal Server Error\r\n'
		client_socket.sendall(response)

		error_id = client_id if client_id else ''
		print(f'ERROR Client [{error_id}]: {e}')

	finally:
		client_socket.close()


# サーバーの接続待ちをする関数
def	run_server(host='127.0.0.1', port=8080):
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	server_socket.bind((host, port))
	server_socket.listen(5)
	print(f'Server listening {host}:{port}')



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
		print('\nServer closing...')
	except Exception as e:
		print(f'ERROR run_server: {e}')
		return
	finally:
		server_socket.close()
		print('server closed')

if __name__ == '__main__':
	run_server()
