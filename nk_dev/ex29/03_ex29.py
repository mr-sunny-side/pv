#!/usr/bin/env python3

import sys
import threading
import socket

"""
	01-15: handle_client関数の結果の出力から

	コマンドを入れると、クライアントのリクエストを表示するスクリプト




	- 実例
	GET /index.html HTTP/1.1
	Host: localhost:8080
	User-Agent: Mozilla/5.0
	Accept: text/html
	Connection: close

"""

client_count = 0
lock = threading.Lock()

# 教訓：　クラス内でのループは次回から行わないこと
class RequestData:
	def __init__(self):
		self.method = None
		self.path = None
		self.version = None
		self.header = {}

	def parse_request(self, request):

		# リクエストを行で分割
		request_lines = request.decode('utf-8', errors='replace').split('\r\n')

		# リクエスト情報を保存
		self.method, self.path, self.version = self.parse_http_line(request_lines[0])

		# この書き方だと、rangeはインデックスにならない
		for i in range(1, len(request_lines)):

			# 空行はヘッダー終端なので、終了
			if request_lines[i] == '':
				break

			# ヘッダー行をパース
			header_name, header_detail = self.parse_header(request_lines[i])
			if not header_name or not header_detail:
				return

			self.header[header_name] = header_detail

	# ヘッダーの各行を辞書に保存
	def	parse_header(self, header_line):
		try:
			# 最初のコロンでパース
			parts = header_line.split(':', 1)

			header_name = parts[0]
			header_detail = parts[1]

			return header_name, header_detail
		except IndexError:
			print('ERROR parse_header/RequestData: Index error')
			return None, None

	# http行をパースして返す
	def	parse_http_line(self, http_line):
		try:
			parts = http_line.split()

			method = parts[0]
			path = parts[1]
			version = parts[2]

			return method, path, version
		except IndexError:
			print('ERROR parse_http_line/RequestData: Index error')
			return None, None, None

def	print_request(request_data, client_id, client_address):
	"""
		============================================================
		[Connection 1] New connection from 127.0.0.1:xxxxx
		============================================================
		[Connection 1] Request Line:
		Method: GET
		Path: /test
		HTTP Version: HTTP/1.1

		[Connection 1] Headers:
		Host: localhost:8080
		User-Agent: curl/7.68.0
		Accept: */*

		[Connection 1] Connection closed

	"""

	print(f'{"=" * 60}')
	print(f'[Connection {client_id}] New connection from {client_address[0]}:{client_address[1]}')
	print(f'{"=" * 60}')

	print(f'[Connection {client_id}] Request Line:')
	print(f'Method: {request_data.method}')
	print(f'Path: {request_data.path}')
	print(f'HTTP Version: {request_data.version}')
	print()

	print(f'[Connection {client_id}] Headers:')
	for label, detail in request_data.header.items():
		print(f'{label}: {detail}')
	print()

	print(f'[Connection {client_id}] Connection closed')


# 接続したクライアントのリクエストを処理
def	handle_client(client_socket, client_address):
	# ヘッダー情報を保存する辞書
	request_data = {}
	global client_count

	try:
		request = client_socket.recv(1024)

		if not request:
			print('ERROR handle_client: Request is empty')
			return

		with lock:
			client_count += 1
			client_id = client_count

		# リクエストデータをパースして保存
		request_data = RequestData()
		request_data.parse_request(request)

		# 結果をプリント
		print_request(request_data, client_id, client_address)

	except Exception as e:
		print(f'ERROR handle_client: {e}')
		return
	finally:
		client_socket.close()

def	create_server_socket(host, port):

	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	server_socket.bind((host, port))
	server_socket.listen(5)

	return server_socket

def run_server(host='127.0.0.1', port=8080):

	server_socket = create_server_socket(host, port)
	print(f'run_server: Server listening {host}:{port}')

	try:
		while True:

			client_socket, client_address = server_socket.accept()
			print(f'run_server: Connection detected {client_address[0]}:{client_address[1]}')

			# 正常終了のレスポンスを送信
			response = b'HTTP/1.1 200 OK\r\n'
			response += b'Content-Type: text/plane\r\n'
			response += b'\r\n'
			response += b'Hello Client !\n'
			client_socket.sendall(response)

			# handle_clientスレッド
			client_thread = threading.Thread(
				target=handle_client,
				args=(client_socket, client_address),
				daemon=True
			)

			client_thread.start()

	except KeyboardInterrupt:
		print('Server Closing')
	finally:
		server_socket.close()
		print('Server Closed')

if __name__ == '__main__':
	run_server()
