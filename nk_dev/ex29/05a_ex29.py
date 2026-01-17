import sys
import threading
import socket

"""
	辞書を使ったルーティングを行い、リクエストパスに対して適切なhtmlを返すサーバー

	01-17:	まずは各ハンドラー関数と、同時に機能するhtmlの型を作成するcreate_html関数の作成
			次にレスポンスクラスと、それをバイト列の完成形として返す内部関数の作成
"""

routes = {
	'/': handle_index,
	'/index.html': hadle_index,
	'/about': handle_about,
	'/time': handle_time
}

def	create_html(title, h1, content):

	html = f"""
	<!DOCTYPE html>
	<html lang="ja">
	<head>
		<meta charset="utf-8">
		<title>{title}</title>
	</head>
	<body>
		<h1>{h1}</h1>
		{content}
	</body>
	</html>

	"""

# サーバーの接続待ちをする関数
def	run_server(host='127.0.0.1', port=8080):
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	server_socket.bind((host, port))
	server_socket.listen(5)

	try:
		while True:
			client_socket, client_address = server_socket.accept()

			# パスによって分岐し、適した関数を呼び出す関数をサブスレッドで起動
	except Exception as e:
		print(f'ERROR run_server: {e}')
		return
	finally:
		server_socket.close()
