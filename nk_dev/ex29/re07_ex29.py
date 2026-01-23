#!/usr/bin/env python3

import sys
import socket
import threading

"""
	01-24:	serve_static関数の記述
			動的パスのルーティング
				- ハンドラーの記述
				- デコレータの記述

			クエリパラメータへの対応追加
				- Requestクラスの属性を追加
				- parse_http関数にクエリのパースを追加
				- /searchパスのハンドラーを追加
				- ハンドルクライアントの修正

			handle_client関数：エラー検出の具体化


"""

def	run_server(host='127.0.0.1', port=8080):
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	server_socket.bind((host, port))
	server_socket.listen(5)
	print(f'Server listening {host}:{port}')
	# ルートの表示

	# サーバーループ
