import re
import html
import logging
import mimetypes
from pathlib import Path

import config
from http import Request
from textwrap import dedent

routes = []
STATIC_DIR = Path(__file__).parent / 'static'
config.setup_logging()

class Response:
	def	__init__(self, status=200, reason='OK', headers=None, body=''):
		self.status = status
		self.reason = reason
		self.headers = headers if headers else {}
		self.body = body

		if 'Connection' not in self.headers:
			headers['Connection'] = 'close'
		if 'Content-Type' not in self.headers:
			headers['Content-Type'] = 'text/html; charset=utf-8'

	def	to_bytes(self):
		response = f'HTTP/1.1 {self.status} {self.reason}\r\n'
		for label, detail in self.headers.items():
			# ヘッダーインジェクション防止
			response += f'{label}: {detail}\r\n'
		response += '\r\n'
		response = response.encode('utf-8', errors='replace')

		if isinstance(self.body, bytes):
			response += self.body
		else:
			response += self.body.encode('utf-8', errors='replace')

		return response

# ルーティング関数
def	route(path: str):
	def	register(handler):
		pattern = re.sub(r'<(\w+)>', r'(?P<\1>[^/]+)', path)
		pattern = f'^{pattern}$'
		routes.append((re.compile(pattern), handler))
		return handler
	return register

def	create_html(title, h1, content):

	# dedent関数を使うと複数行のcontentへの対応が複雑化するので却下
	html = [
		'<!DOCTYPE html>',
		'<html lang="ja">',
		'<head>',
		'\t<meta charset="utf-8">',
		f'\t<title>{title}</title>',
		'</head>',
		'<body>',
		f'\t<h1>{h1}</h1>',
		content,
		'</body>',
		'</html>'
	]

	return '\n'.join(html)

@route('/')
def handle_html(**kwargs) -> Response:	# ハンドラー捜索の際、一貫してアンパック引数を渡す
	file_path = STATIC_DIR / 'index.html'
	file_path = file_path.resolve()
	body = file_path.read_text('utf-8')
	length = len(body.encode('utf-8', errors='replace'))

	return Response(
		status=200,
		reason='OK',
		headers={
			'Content-Type': 'text/html; charset=utf-8',
			'Content-Length': length
		},
		body=body
	)

@route('/about')
def	handle_about(**kwargs) -> Response:
	file_path = STATIC_DIR / 'about.html'
	file_path = file_path.resolve()
	body = file_path.read_text('utf-8')
	length = len(body.encode('utf-8', errors='replace'))

	return Response(
		status=200,
		reason='OK',
		headers={
			'Content-Type': 'text/html; charset=utf-8',
			'Content-Length': length
		},
		body=body
	)

@route('/user/<user_id>')
def	handle_user(user_id: str, **kwargs) -> Response:
	user_id = html.escape(user_id)
	title = 'User Page'
	h1 = f'Welcome {user_id} !'
	content = '\t<p>これはユーザーページのダミーです</p>\n'

	body = create_html(title, h1, content)
	length = len(body.encode('utf-8', errors='replace'))

	return Response(
		status=200,
		reason='OK',
		headers={
			'Content-Type': 'text/html; charset=utf-8',
			'Content-Length': length
		},
		body=body
	)

@route('/search')
def	handle_search(request_obj: Request, **kwargs) -> Response:
	title = 'Search Page'
	h1 = 'Search Page'
	content = '\t<p>これは検索ページのダミーです</p>\n'
	content += '\t<p>以下はあなたが入力したクエリです</p>\n'
	content += '\t<ul>\n'


	for label, detail in request_obj.query.items():
		label = html.escape(label)
		detail = ','.join(detail)
		detail = html.escape(detail)
		content += f'\t\t<li>{label}: {detail}</li>\n'
	content += '\t</ul>\n'

	body = create_html(title, h1, content)
	length = len(body.encode('utf-8', errors='replace'))

	return Response(
		status=200,
		reason='OK',
		headers={
			'Content-Type': 'text/html; charset=utf-8',
			'Content-Length': length
		},
		body=body
	)

# POSTメソッドに対して入力内容をミラーしたhtmlを作成する
def	handle_post_method(request_obj: Request) -> Response:
	title = 'POST Handler'
	h1 = '200 OK'
	content = '\t<p>POSTメソッドは正常に処理されました</p>\n'
	content += '\t<p>以下はあなたが入力したリクエストボディです</p>\n'
	content += '\t<ul>\n'


	for label, detail in request_obj.body.items():
		label = html.escape(label)
		detail = ','.join(detail)
		detail = html.escape(detail)
		content += f'\t\t<li>{label}: {detail}</li>\n'
	content += '\t<ul>\n'

	body = create_html(title, h1, content)
	length = len(body.encode('utf-8', errors='replace'))

	return Response(
		status=200,
		reason='OK',
		headers={
			'Content-Type': 'text/html; charset=utf-8',
			'Content-Length': length
		},
		body=body
	)


def static_search(path: str) -> Response | None:
	# file_path変数を作成
	path = path.lstrip('/')
	file_path = STATIC_DIR / path
	file_path = file_path.resolve()

	# セキュリティチェック
	try:
		if not str(file_path).startswith(str(STATIC_DIR.resolve())):
			logging.warning('static_search: Invalid path')
			return None
	except Exception as e:
		logging.warning('Exception static_search: Invalid path')
		return None

	# パスが存在するか確認
	if not file_path.exists() or not file_path.is_file():
		logging.info('static_search: path is not exists or not file')
		return None

	# ファイル形式の確認
	mime_type, _ = mimetypes.guess_type(file_path)
	if not mime_type:
		mime_type = 'application/octet-stream'	# ファイル形式が不明なら記述

	# ファイルの読み込み
	try:
		if mime_type.startswith('text/') or \
			mime_type in ['application/javascript', 'application/json']:
			body = file_path.read_text('utf-8')
			length = len(body.encode('utf-8', errors='replace'))
		else:
			body = file_path.read_bytes()
			length = len(body)
	except IOError:
		logging.error('static_search: Cannot read the file')
		return None
	except Exception as e:
		logging.error('Exception static_search: Cannot read the file')
		return None

	return Response(
		status=200,
		reason='OK',
		headers={
			'Content-Type': mime_type,
			'Content-Length': length
		},
		body=body
	)
