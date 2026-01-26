import sys
import socket
import threading

from http import get_request, parse_http

"""
	POSTメソッドに対応するサーバー
	08_ex29.py:
		- run_server関数
		- handle_client関数

	01-26:	http.py の記述を完了
			POST、GETメソッドそれぞれリクエスト取得の確認から

"""

client_count = 0
lock = threading.Lock()

def	handle_client(client_socket, client_address):
	try:
		# idを付与
		with lock:
			client_count += 1
			client_id = client_count
		print('handle_client: Connection detected')
		print(f'\t{client_address[0]}:{client_address[1]} id={client_id}')

		# リクエスト情報を取得
		if get_request(client_socket) == 1:
			raise ValueError

		# POSTとGETで分岐
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
