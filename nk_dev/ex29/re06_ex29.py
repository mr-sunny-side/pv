#!/ust/bin/env python3

import re
import sys
import socket
import threading

from pathlib import Path
import mimetypes

"""
	ex29_06の復習
	01-22:	serve_static関数の記述 - 進行中
			動的パスのルーティング
			handle_client関数の記述,エラー検出の具体化
			staticディレクトリにhtmlを格納
			クエリパラメータへの対応追加


"""

client_count = 0
routes = []
lock = threading.Lock()

STATIC_DIR = Path(__file__).parent() / 'static'

class Request:
	def	__init__(self):
		self.method = None
		self.path = None
		self.version = None

class Response:
	def	__init__(self, status=200, reason='OK', headers={}, body=''):
		self.status = status
		self.reason = reason
		self.headers = headers
		self.body = body

		if 'Content-Type' not in self.headers:
			self.headers['COntent-Type'] = 'text/html; charset=utf-8'
		if 'Connection' not in self.headers:
			self.headers['Connection'] = 'close'

	def	to_bytes(self):
		response = f'HTTP/1.1 {self.status} {self.reason}\r\n'

		for label, detail in self.headers.items():
			response += f'{label}: {detail}\r\n'
		response_bytes = response.encode('utf-8', errors='replace')	#一旦ヘッダーまでエンコード

		# bodyのエンコード
		if isinstance(self.body, bytes):
			response_bytes += self.body
		else:
			response_bytes += self.body.encode('utf-8', errors='replace')

		return response_bytes

def	parse_http(http_line, request_obj):

	parts = http_line.split()
	if len(parts) != 3:
		return False

	request_obj.method, request_obj.path, request_obj.version = parts
	return True

def	serve_static(path):

	# パスを絶対パスに変換
	file_path = path.lstrip('/')
	file_path = STATIC_DIR / file_path
	file_path = file_path.resolve()

	# セキュリティチェック(ディレクトリトラバーサル対策)
	try:
		if not str(file_path).startswith(str(STATIC_DIR.resolve())):
			print(f'Warning serve_static: This path is invalid', file=sys.stderr)
			return None
	except Exception as e:
		print(f'Warning serve_static: {e}', file=sys.stderr)
		return None

	# ファイルパスの存在、ファイルかどうかの検証
	if not file_path.exists() or not file_path.is_file():
		print(f'serve_static: This path is not exist or dir', file=sys.stderr)
		return None

	# ファイルタイプの確認
	mime_type, _ = mimetypes.guess_type(str(file_path))
	if not mime_type:
		mime_type = 'application/octet-stream'

	# 適したリードメソッドを呼ぶ
	if mime_type.startswith('text/') or \
		mime_type in ['application/javascript', 'application/json']:
		body = file_path.read_text(encoding='utf-8')
	else:
		body = file_path.read_bytes()


def	handle_client(client_socket, client_address):
	"""
	適切なエラー検出を模索
	静的ファイルリクエスト、ハンドラーループの記述から

	"""
	global client_count

	try:
		with lock:
			client_count += 1
			client_id = client_count
		print(f'handle_client: Connection detected id={client_id}', file=sys.stderr)

		raw_data = client_socket.recv(4096)

		# リクエストデータが空なら終了
		if not raw_data:
			print('Warning handle_client: Request is empty', file=sys.stderr)
			return

		# リクエストをエンコードしてhttpリクエストを保存
		request_line = raw_data.decode('utf-8', errors='replace').split('\r\n')
		request_obj = Request()
		if not parse_http(request_line[0], request_obj):
			print(f'ERROR parse_http/handle_client: Cannot parse http request')
			raise ValueError

		# 静的ファイルの捜索
		# 静的ファイルではない場合、ハンドラーの捜索

	except ValueError as e:
		print(e)
	finally:
		client_socket.close()


def	run_server(host='127.0.0.1', port=8080):
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	server_socket.bind((host, port))
	server_socket.listen(5)
	print(f'Server listening {host}:{port}', file=sys.stderr)
	# ルート、staticの表示

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
		print('\nServer closing', file=sys.stderr)
	finally:
		server_socket.close()
		print('Server closed', file=sys.stderr)

if __name__ == '__main__':
	run_server()
