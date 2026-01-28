import re
import html
import mimetypes
from pathlib import Path

routes = []

STATIC_DIR = Path(__file__).parent / 'static'

class Response:
	def __init__(self, status=200, reason='OK', headers=None, body=''):
		self.status		= status
		self.reason		= reason
		self.headers	= headers if headers else {}
		self.body 		= body

		if 'Content-Type' not in self.headers:
			self.headers['Content-type'] = 'text/html; charset=utf-8'
		if 'Connection' not in self.headers:
			self.headers['Connection'] = 'close'

	def to_bytes(self):

		response = f'HTTP/1.1 {self.status} {self.reason}\r\n'
		for label, detail in self.headers.items():
			response += f'{label}: {detail}\r\n'

		response += '\r\n'
		response = response.encode('utf-8',errors='replace')

		if isinstance(self.body, bytes):
			response += self.body
		else:
			response += self.body.encode('utf-8', errors='replace')

		return response

def	static_search(path) -> Response | None:

	# ファイルパスを絶対パスに変換
	file_path = path.lstrip('/')
	file_path = STATIC_DIR / file_path
	file_path = file_path.resolve()

	# セキュリティチェック
	try:
		if not str(file_path).startswith(str(STATIC_DIR.resolve())):
			print('Warning static_search: Invalid path')
			return None
	except Exception as e:
		print('ERROR static_search: Invalid path')
		print(e)
		return None

	# パスが存在するか、ファイルか確認
	if not file_path.exists() or not file_path.is_file():
		print('static_search: path is not exist or not file')
		return None

	# ファイルの形式を確認
	mime_types, _ = mimetypes.guess_type(file_path)
	if not mime_types:
		mime_types = 'application/octet-stream'

	# bodyの読み込み
	if mime_types.startswith('text/') or \
		mime_types in ['application/javascript', 'application/json']:
		body	= file_path.read_text('utf-8')
		length	= len(body.encode('utf-8', errors='replace'))
	else:
		body	= file_path.read_bytes()
		length	= len(body)

	return Response(
		status=200,
		reason='OK',
		headers={
			'Content-Type': mime_types,
			'Content-Length': length
		},
		body=body
	)

def	search_route(request_obj) -> Response | None:

	global routes
	for pattern, handler in routes:
		matched = pattern.match(request_obj.path)
		if matched:
			param = matched.groupdict()
			param['request_obj'] = request_obj
			response_obj = handler(**param)
			return response_obj
	return None


def	route(path):
	def	register(handler):

		pattern = re.sub(r'<(\w+)>', r'(?P<\1>[^/]+)', path)
		pattern = f'^{pattern}$'
		routes.append((re.compile(pattern), handler))

		return handler
	return register

def	create_html(title, h1, content) -> str:

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
		'</html>',
	]

	body = '\n'.join(html)
	return body

@route('/')
def	handle_html(**kwargs):

	file_path	= STATIC_DIR / 'index.html'
	file_path	= file_path.resolve()
	body		= file_path.read_text('utf-8')
	length		= len(body.encode('utf-8',errors='replace'))

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
def	handle_about(**kwargs):

	file_path	= STATIC_DIR / 'about.html'
	file_path	= file_path.resolve()
	body		= file_path.read_text('utf-8')
	length		= len(body.encode('utf-8', errors='replace'))

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
def	handle_search(request_obj, **kwargs):

	title	= 'Search Page'
	h1		= 'Search Page'
	content = '\t<p>このページは検索ページのダミーページです</p>\n'
	content += '\t<p>以下はあなたが入力したクエリです</p>\n'
	content += '\t<ul>\n'
	for label, detail in request_obj.query.items():
		label	= html.escape(label)
		detail	= ','.join(detail)
		detail	= html.escape(detail)
		content += f'\t\t<li>{label}: {detail}</li>\n'

	content	+= '\t</ul>\n'
	body 	= create_html(
		title=title,
		h1=h1,
		content=content
	)
	length	= len(body.encode('utf-8', errors='replace'))

	return	Response(
		status=200,
		reason='OK',
		headers={
			'Content-Type': 'text/html; charset=utf-8',
			'Content-Length': length
		},
		body=body
	)


@route('/user/<user_id>')
def	handle_user(user_id, **kwargs):

	user_id = html.escape(user_id)
	content = f'\t<p>ようこそ {user_id} !</p>\n'
	content = f'\t<p>これはユーザー専用のダミーページです</p>\n'
	body = create_html(
		title=f'User Page',
		h1=f'Welcome {user_id} !',
		content=content
	)

	length = len(body.encode('utf-8', errors='replace'))
	return	Response(
		status=200,
		reason='OK',
		headers={
			'Content-Type': 'text/html; charset=utf-8',
			'Content-Length': length
		},
		body=body
	)

def	handle_post_method(**kwargs) -> Response:

	body	= 'POSTメソッドは正常に処理されました\n'
	length	= len(body.encode('utf-8', errors='replace'))
	return	Response(
		status=200,
		reason='OK',
		headers={
			'Content-Type': 'text/plain',
			'Content-Length': length,
		},
		body=body
	)

def	handle_404(**kwargs):

	body	= create_html(
		title='404 Not Found',
		h1='404 Not Found',
		content='\t<p>そのパスは存在しません</p>'
	)

	length 	= len(body.encode('utf-8', errors='replace'))
	return	Response(
		status=404,
		reason='Not Found',
		headers={
			'Content-Type': 'text/html; charset=utf-8',
			'Content-Length': length
		},
		body=body
	)
