from urllib.parse import urlparse, parse_qs

"""
	リクエストの取得を行うファイル
	http.py:
		- Requestクラス
		- parse_http関数
		- get_header関数

"""

class Request:
	def	__init__(self):
		self.method		= None
		self.path		= None
		self.version	= None
		self.query		= {}
		self.length		= None
		self.body		= ''

def	parse_http(http_line: str, request_obj: Request) -> bool:

	parts = http_line.split()
	if len(parts) != 3:
		return False

	request_obj.method = parts[0]
	request_obj.version = parts[2]

	url = urlparse(parts[1])
	request_obj.path = url.path
	request_obj.query = parse_qs(url.query)
	return True

def	get_request(client_socket) -> int:
	# ヘッダー終了読み込みまでループ
	buffer = b''
	while b'\r\n\r\n' not in buffer:
		buffer += client_socket.recv(4096)
		if not buffer:		# 空なら切断
			print('Warning handle_client: Request is empty')
			return -1

	# \r\nを見つけてそこで分離
	header_end	= buffer.find(b'\r\n\r\n')
	header		= buffer[:header_end - 1]	# ヘッダー終了文字を除いてヘッダーを保存
	body_parts	= buffer[header_end + 4:]	# スライス記法では範囲外のアクセスでエラーにならない

	# ヘッダーはこれから追加されないのでデコード
	header = header.decode('utf-8', errors='replace')

	## httpヘッダーを保存
	request_obj			= Request()
	header_line			= header.split('\r\n')
	if not parse_http(header_line[0], request_obj):
		print(f'ERROR parse_http/get_header: http_line')
		return 1

	# GETメソッドならここで終了
	if request_obj.method == 'GET':
		return 0

	## bodyの取得
	# body長を取得
	for header in header_line[1:]:
		if 'Content-Length' in header:
			request_obj.length = header.split(':')[1].strip()
			break

	# body長を取得できなかったらエラー
	if not request_obj.length:
		print('ERROR get_header: Cannot find Content-Length in POST method')
		return 1

	# content-lengthの値から残りのbodyを読み込み
	while len(body_parts) < request_obj.length:
		buffer = client_socket.recv(4096)
		if not buffer:
			break
		body_parts += buffer

	# bodyをデコードして保存
	request_obj.body = body_parts.decode('utf-8',errors='replace')
	return 0
