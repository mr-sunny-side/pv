import sys
import socket
import logging
import threading

import config

"""
	08_ex29に09の機能を追加したサーバー
	08_ex29/md/improvement_guide.md を読んで機能を追加

	01-28:	get_request関数の記述から


"""

client_count = 0
lock = threading.Lock()
config.setup_logging()


def	handle_client(client_socket, client_address):
	global client_count
	try:
		client_socket.settimeout(config.TIMEOUT_INT)	# timeoutの設定
		with lock:								# ユーザーIDの付与
			client_count += 1
			client_id = client_count
		logging.info('handle_client: Connection detected')
		logging.info(f'\t{client_address[0]}:{client_address[1]} id={client_id}')

		# get_request


	except ValueError as e:
		logging.error(f'ValueError handle_client:')
		logging.error(e)
		# 400 Bad Request
	except socket.timeout:
		logging.warning('handle_client: Client timeout')
		# 408 Request Timeout
	except ConnectionError as e:
		logging.error('handle_client: Client connection error')
		logging.error(e)
	except Exception as e:
		logging.error(f'Exception handle_client:')
		logging.error(e)
		# 500 Internal Error
	finally:
		client_socket.close()


def	run_server(host=config.LOCAL_HOST, port=config.PORT):
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
