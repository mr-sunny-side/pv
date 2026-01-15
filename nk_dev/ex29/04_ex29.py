#!/usr/bin/env python3

"""
	HTTPクライアントのリクエストパスに応じて返答するサーバー

	01-15: クラスとhandle_client関数の記述から
"""

import sys
import threading
import socket

client_count = 0

class RequestData:
	def	__init__(self):
		self.method = None
		self.path = None
		self.version = None
		self.header = {}

	# httpリクエスト、ヘッダーをパースする関数

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

			# handle_client関数
			# リクエストの解析と適切な応答
	except KeyboardInterrupt:
		print('Server Closing...')
	finally:
		server_socket.close()
		print('Server closed')
