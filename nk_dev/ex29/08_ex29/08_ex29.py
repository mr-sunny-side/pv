#!/usr/bin/env python3

import sys
import socket
import threading

from http import get_request, print_request, Request
from route import handle_post_method, handle_404, static_search, search_route

"""
	POSTメソッドに対応するサーバー
	08_ex29.py:
		- run_server関数
		- handle_client関数

	01-26:	static_search関数のエラー出力が暴発するのを修正
			searchパスがBad Requestになるエラーを修正
			POSTメソッドの確認

			searchパスのエラー現状
			- curl "http://localhost:8080/search?q=python&test=hello&test=server&greetings=Hello+Server"
			- ValueError handle_client: not enough values to unpack (expected 2, got 1)

			POST、GETメソッドそれぞれリクエスト取得の確認	- 完了
			POSTメソッドに対するレスポンス					- 完了
			GETメソッドに対するルートレスポンス				- 完了



"""

client_count	= 0
lock			= threading.Lock()

def	handle_client(client_socket, client_address):

	global client_count
	try:
		# idを付与
		with lock:
			client_count	+= 1
			client_id		= client_count
		print()
		print('handle_client: Connection detected')
		print(f'\t{client_address[0]}:{client_address[1]} id={client_id}')

		# リクエスト情報を取得
		request_obj	= Request()
		result		= get_request(client_socket, request_obj)
		if result == 1:		# 400として処理
			raise ValueError
		elif result == -1:	# 切断として終了
			return

		# リクエスト内容を出力
		print_request(request_obj)

		# POSTメソッドなら200として処理
		if request_obj.method == 'POST':
			response_obj	= handle_post_method()
			response_bytes	= response_obj.to_bytes()
			client_socket.sendall(response_bytes)
			return

		## GETメソッドの処理
		# 静的ファイルの捜索
		static_data = static_search(request_obj.path)
		if static_data:
			response_obj	= static_data
			response_bytes	= response_obj.to_bytes()
			client_socket.sendall(response_bytes)
			return

		# 静的ファイル出ない場合、ハンドラーを捜索
		handler_data = search_route(request_obj)
		if handler_data:
			response_obj	= handler_data
			response_bytes	= response_obj.to_bytes()
			client_socket.sendall(response_bytes)
			return

		# 静的ファイル、ハンドラー捜索で引っかからないなら404
		response_obj	= handle_404()
		response_bytes	= response_obj.to_bytes()
		client_socket.sendall(response_bytes)
		return
	except ValueError as e:
		print(f'ValueError handle_client: {e}')

		response = b'HTTP/1.1 400 Bad Request\r\n'
		response += b'Content-Type: text/plain\r\n'
		response += b'Connection: close\r\n'
		response += b'\r\n'
		response += b'400 Bad Request\n'
		client_socket.sendall(response)
	except Exception as e:
		print(f'ERROR Exception handle_client: {e}')

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
	print(f'Server listening {host}:{port}')
	# ルートの出力

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
		print('server closed')

if __name__ == '__main__':
	run_server()
