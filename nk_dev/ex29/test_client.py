#!/usr/bin/env python3

import time
import socket

try:
	# IPv4, TCP
	# ソケット関数に上書きしない変数名にすること
	client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	# ローカルホストのhttpに接続
	client_socket.connect(('127.0.0.1', 8080)) # ipアドレスは文字列として引数に入力

	# サーバーにバイト列を送る
	client_socket.sendall(b'Hello　Server!\n')

	#　バッファにサーバーからの送信を保存
	while True:
		response = client_socket.recv(1024)

	# サーバーの送信を表示
	print(f'Server response: {response.decode("utf-8")}')

finally:
	# 通信が終わったらソケットを閉じる
	client_socket.close()

