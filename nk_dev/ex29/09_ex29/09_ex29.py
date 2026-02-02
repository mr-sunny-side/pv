#!/usr/bin/env python3

import sys
import socket
import logging
import threading

import config
from http import Request, get_request, print_request
from route import routes, static_search, handle_post_method
from error import handle_400, handle_404, handle_408, handle_500

"""
	POST, GETメソッドに対応したサーバー
	08_ex29/md/improvement_guide.md を読んで機能を追加

	02-01:	各エラーのハンドラー記述から

			ヘッダーインジェクションの防止記述(to_bytesメソッド)
			run_server関数で最初にルートの表示
			handle_client関数でエラー送信の記述


"""

client_count = 0
lock = threading.Lock()
config.setup_logging()


def	handle_client(client_socket, client_address):
	global client_count
	try:
		client_socket.settimeout(config.TIMEOUT_INT)	# timeoutの設定
		with lock:
			client_count += 1
			client_id = client_count	# ユーザーIDの付与
		logging.info('')
		logging.info('handle_client: Connection detected')
		logging.info(f'\t{client_address[0]}:{client_address[1]} id={client_id}')

		# get_request関数でリクエスト情報を保存
		request_obj = Request()
		if get_request(client_socket, request_obj) == -1:
			logging.error('get_request/handle_client: returned error')
			raise ValueError

		# リクエスト情報を出力
		print_request(request_obj)

		# POSTならhandle_post関数でレスポンス
		if request_obj.method == 'POST':
			response_obj = handle_post_method(request_obj)
			response_bytes = response_obj.to_bytes()
			client_socket.sendall(response_bytes)
			return

		# 静的ファイルの捜索
		static_data = static_search(request_obj.path)
		if static_data:
			response_obj = static_data
			response_bytes = response_obj.to_bytes()
			client_socket.sendall(response_bytes)
			return

		# パスがstatic_dirになければハンドラーを探す
		for pattern, handler in routes:
			matched = pattern.match(request_obj.path)
			if matched:
				kwargs = matched.groupdict()
				kwargs['request_obj'] = request_obj	# Requestを使うハンドラーのために辞書に追加
				response_obj = handler(**kwargs)
				response_bytes = response_obj.to_bytes()
				client_socket.sendall(response_bytes)
				return

		# ハンドラーも見つからなければ404処理
		response_obj = handle_404()
		response_bytes = response_obj.to_bytes()
		client_socket.sendall(response_bytes)
		return

	except ValueError as e:
		logging.error(f'ValueError handle_client:')
		logging.error(e)

		# 400 Bad Request
		response_obj = handle_400()
		response_bytes = response_obj.to_bytes()
		client_socket.sendall(response_bytes)
	except socket.timeout:
		logging.warning('handle_client: Client timeout')

		# 408 Request Timeout
		response_obj = handle_408()
		response_bytes = response_obj.to_bytes()
		client_socket.sendall(response_bytes)
	except ConnectionError as e:
		logging.error('handle_client: Client connection error')
		logging.error(e)
	except Exception as e:
		logging.error(f'Exception handle_client:')
		logging.error(e)

		# 500 Internal Error
		response_obj = handle_500()
		response_bytes = response_obj.to_bytes()
		client_socket.sendall(response_bytes)
	finally:
		client_socket.close()


def	run_server(host=config.LOCAL_HOST, port=config.PORT):
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	server_socket.bind((host, port))
	server_socket.listen(5)
	logging.info('')
	logging.info(f'Server Listening {host}:{port}')
	logging.info('routes:')
	for pattern, handler in routes:
		logging.info(f'\t{pattern.pattern:<30}:{handler.__name__:>10}')


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

if __name__ == '__main__':
	run_server()
