#!/usr/bin/env python3

"""
	HTTPクライアントのリクエストパスに応じて返答するサーバー

	01-15: claudeに評価してもらうところから
"""

import sys
import threading
import socket
from datetime import datetime

client_count = 0
lock = threading.Lock()

class RequestData:
	def	__init__(self):
		self.method = None
		self.path = None
		self.version = None
		self.header = {}


	# httpリクエストをパースする関数
	def	parse_http(self, http_line):
		parts = http_line.split()

		if len(parts) != 3:
			return False

		self.method = parts[0]
		self.path = parts[1]
		self.version = parts[2]

		return True

	# ヘッダー情報を行ごとにパースする関数
	def	parse_header(self, header_lines):
		for line in header_lines:
			if not line.strip():	# 空行なら終了
				break
			if ':' in line:			# コロンがあったらパース
				key, value = line.split(':', 1)

			self.header[key.strip()] = value.strip()	# パースしたヘッダーを辞書に保存

	# リクエスト全体のパースエラーを捕捉する関数
	def	parse_request(self, request):
		lines = request.split('\r\n')

		try:
			if not self.parse_http(lines[0]):	# httpリクエストがパースできなければエラーを吐く
				raise ValueError

			# ヘッダーを保存
			self.parse_header(lines[1:])
			return True
		except ValueError as e:
				print(f'ERROR parse_request: {e}')
				return

def	create_html(path):

	response = b'HTTP/1.1 200 OK\r\n'
	response += b'Content-Type: text/html; charset=utf-8\r\n'

	if path == '/' or path == '/index.html':
		html = """<!DOCTYPE html>
		<html lang="ja">
		<head>
			<meta charset="utf-8">
			<title>Welcome</title>
		</head>
		<body>
			<h1>Welcome to My HTTP Server</h1>
			<p>このページはpythonで作られたindex.htmlのページです。</p>
			<p>パスを変えてアクセスしてみてください：</p>
			<ul>
				<li>/about</li>
				<li>/time</li>
				<li>/test</li>
			</ul>
		</body>
		</html>
		"""

		# コンテンツの長さはエンコード後に増えることに留意

		html_length = len(html.encode('utf-8', errors='replace'))
		content_length = f'Content-Length: {html_length}\r\n'

		response += content_length.encode('utf-8', errors='replace')
		response += b'\r\n'
		response += html.encode('utf-8', errors='replace')
		return response

	elif path == '/about':
		html = """<!DOCTYPE html>
		<html lang="ja">
		<head>
			<meta charset="utf-8">
			<title>About</title>
		</head>
		<body>
			<h1>About this server</h1>
			<p>このサーバーはpythonによるHTTPサーバーの学習の一環で作成しました。</p>
			<ul>
				<li>TCP ソケットによる通信</li>
				<li>threadingモジュールによる複数クライアントへの対応</li>
				<li>HTTPリクエストに対するレスポンス</li>
			</ul>
		</body>
		</html>
		"""

		html_length = len(html.encode('utf-8', errors='replace'))
		content_length = f'Content-Length: {html_length}\r\n'

		response += content_length.encode('utf-8', errors='replace')
		response += b'\r\n'
		response += html.encode('utf-8', errors='replace')
		return response


	elif path == '/time':
		current_time = datetime.now().strftime('%Y-%m-%d')

		html = f"""<!DOCTYPE html>
		<html lang="ja">
		<head>
			<meta charset="utf-8">
			<title>Current time</title>
		</head>
		<body>
			<h1>The current server time</h1>
			<p>現在のサーバー時間を表示します</p>
			<p>{current_time}</p>
		</body>
		</html>
		"""

		html_length = len(html.encode('utf-8', errors='replace'))
		content_length = f'Content-Length: {html_length}\r\n'

		response += content_length.encode('utf-8', errors='replace')
		response += b'\r\n'
		response += html.encode('utf-8', errors='replace')
		return response

	else:
		response = b'HTTP/1.1 404 Not Found\r\n'
		response += b'Content-Type: text/html; charset=utf-8\r\n'

		html = """<!DOCTYPE html>
		<html lang="ja">
		<head>
			<meta charset="utf-8">
			<title>404 Not Found</title>
		</head>
		<body>
			<h1>404 Not Found</h1>
			<p>そのパスのページは存在しません</p>
		</body>
		</html>
		"""

		html_length = len(html.encode('utf-8', errors='replace'))
		content_length = f'Content-Length: {html_length}\r\n'

		response += content_length.encode('utf-8', errors='replace')
		response += b'\r\n'
		response += html.encode('utf-8', errors='replace')
		return response



def	handle_client(client_socket, client_address):
	global client_count

	try:
		request = client_socket.recv(4096)
		request = request.decode('utf-8',errors='replace')

		# リクエストデータをブジェクトとして保存
		# 失敗したら関数を終了
		request_data = RequestData()
		if not request_data.parse_request(request):
			print('ERROR parse_request/handle_client: returned error', file=sys.stderr)
			return

		# クライアントIDを付与
		with lock:
			client_count += 1
			client_id = client_count

		print(f'Client [{client_id}]: {request_data.path}')

		# パスに応じたhtmlを作成
		response = create_html(request_data.path)

		client_socket.sendall(response)
	except Exception as e:
		error_id = client_id if client_id else ''	# クライアントID付与後のエラーならエラーIDとして出力

		print(f'Connection [{error_id}]: {e}', file=sys.stderr)
		response = b'HTTP/1.1 500 Internal Server Error\r\n'
		response += b'Content-Type: text/plain\r\n'
		response += b'Connection: close\r\n'
		response += b'\r\n'
		response += b'Server Error 500'

		client_socket.sendall(response)
	finally:
		client_socket.close()



def	run_server(host='127.0.0.1', port=8080):

	# ソケットの作成
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	server_socket.bind((host, port))
	server_socket.listen(5)
	print(f'run_server: Server is listening')
	print(f'{host}:{port}')
	print()

	try:
		while True:
			client_socket, client_address = server_socket.accept()
			print(f'run_server: Connection detected {client_address[0]}:{client_address[1]}')

			client_thread = threading.Thread(
				target=handle_client,
				args=(client_socket, client_address),
				daemon=True
			)

			client_thread.start()

	except KeyboardInterrupt:
		print('Server Closing...')
	finally:
		server_socket.close()
		print('Server closed')
		return 0

if __name__ == '__main__':
	run_server()
