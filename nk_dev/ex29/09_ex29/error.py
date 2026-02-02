from route import Response, create_html


def	handle_400():
	title = '400 Bad Request'
	h1 = '400 Bad Request'
	content = '\t<p>400 Bad Request</p>\n'

	body = create_html(title, h1, content)
	length = len(body.encode('utf-8', errors='replace'))

	return Response(
		status=400,
		reason='Bad Request',
		headers={
			'Content-Type': 'text/html; charset=utf-8',
			'Content-Length': length
		},
		body=body
	)

def	handle_404():
	title = '404 Not Found'
	h1 = '404 Not Found'
	content = '\t<p>404 Not Found</p>\n'

	body = create_html(title, h1, content)
	length = len(body.encode('utf-8', errors='replace'))

	return Response(
		status=404,
		reason='Not Found',
		headers={
			'Content-Type': 'text/html; charset=utf-8',
			'Content-Length': length
		},
		body=body
	)

def handle_408():
	title = '408 Request Timeout'
	h1 = '408 Request Timeout'
	content = '\t<p>408 Request Timeout</p>\n'

	body = create_html(title, h1, content)
	length = len(body.encode('utf-8', errors='replace'))

	return Response(
		status=408,
		reason='Request Timeout',
		headers={
			'Content-Type': 'text/html; charset=utf-8',
			'Content-Length': length
		},
		body=body
	)

def	handle_500():
	title = '500 Internal Server Error'
	h1 = '500 Internal Server Error'
	content = '\t<p>500 Internal Server Error</p>\n'

	body = create_html(title, h1, content)
	length = len(body.encode('utf-8', errors='replace'))

	return Response(
		status=500,
		reason='Internal Server Error',
		headers={
			'Content-Type': 'text/html; charset=utf-8',
			'Content-Length': length
		},
		body=body
	)
