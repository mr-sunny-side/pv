import sys
import socket
import logging
import threading

"""
	08_ex29に09の機能を追加したサーバー
	08_ex29/md/improvement_guide.md を読んで機能を追加

	01-28:	handle_client関数の記述から


"""
LOCAL_HOST = '127.0.0.1'
BUFFER_SIZE = 4096
TIMEOUT_INT = 30.0
PORT = 8080


client_count = 0
lock = threading.Lock()

def	handle_client(client_socket, client_address):
	global client_count
	try:
		client_socket.settimeout(TIMEOUT_INT)	# timeoutの設定
		with lock:								# ユーザーIDの付与
			client_count += 1
			client_id = client_count
		logging.info('handle_client: Connection detected')
		logging.info(f'\t{client_address[0]}:{client_address[1]} id={client_id}')



	except ValueError as e:
		logging.error(f'ValueERROR handle_client: {e}')
		# 400 Bad Request
	except socket.timeout:
		logging.warning('Warning handle_client: Client timeout')
		# 408 Request Timeout
	except ConnectionError as e:
		logging.warning('Warning handle_client: Client connection error')
		logging.warning(e)
	except Exception as e:
		logging.error(f'Exception ERROR handle_client: {e}')


def	run_server(host=LOCAL_HOST, port=PORT):
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	server_socket.bind((host, port))
	server_socket.listen(5)
	logging.info()
	logging.info(f'Server Listening {host}:{port}')
	# ルートの表示

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
		logging.info('Server closing')
	finally:
		server_socket.close()
		logging.info('Server closed')
