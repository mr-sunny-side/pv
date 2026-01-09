#!/usr/bin/env python3

import socket

# IPv4, TCP
socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# ローカルホストのhttpに接続

socket.connect(('127.0.0.1', 8080))　# ipアドレスは文字列として引数に入力

# サーバーにバイト列を送る
client.sendall(b'HellServer\n')

#　バッファにサーバーからの送信を保存
response = client.recv(1024)

# サーバーの送信を表示
print(f'Server response: {response.decode("utf-8")}')

# 通信が終わったらソケットを閉じる
client.close()
    
