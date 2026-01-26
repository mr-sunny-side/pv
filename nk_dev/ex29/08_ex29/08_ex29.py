import sys
import socket
import threading

"""
	POSTメソッドに対応するサーバー
	08_ex29.py:
		- run_server関数
		- handle_client関数

	01-26: handle_client関数の記述から

"""

client_count = 0
lock = threading.Lock()

def	handle_client(client_socket, client_address):
	try:
		data



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
