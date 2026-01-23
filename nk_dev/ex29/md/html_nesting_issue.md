# HTML生成時のネストとインデントの問題

## 問題点

### 1. curlコマンドでのスペースのエラー

```bash
curl "http://localhost:8080/search?q=python&greetings=hello server"
```

このコマンドだと、スペースが含まれているためURLとして不正です。

**解決策**: スペースを`%20`にURLエンコードする

```bash
curl "http://localhost:8080/search?q=python&greetings=hello%20server"
```

### 2. HTMLのネストが正しく表示されない問題

現在のコード（問題あり）:

```python
@route('/search')
def	handle_search(request: Request):

	body = """
	<!DOCTYPE html>
	<html lang="ja">
	<head>
	\t<meta charset="utf-8">
	\t<title>Search</title>
	</head>
	<body>
	\t<h1>Search Page</h1>
	\t<p>以下はリクエストされたクエリです</p>
	\t<ul>
	"""

	for label, detail in request.query.items():
		label = html.escape(label)
		detail = html.escape(' '.join(detail))
		body += f'\t\t<li>{label}: {detail}</li>\n'

	body += """
	\t</ul>
	</body>
	</html>
	"""

	return body
```

**問題の原因**:

複数行文字列（`"""`）を使う場合、**Pythonコード自体のインデント（タブやスペース）も文字列の一部になる**ため、HTMLのインデントが意図通りにならない。

例えば、この行:
```python
	<!DOCTYPE html>
```

実際には、関数内のインデント用のタブが文字列の先頭に追加されます。

## 解決策

### 方法1: 複数行文字列を左寄せにする（推奨）

```python
@route('/search')
def	handle_search(request: Request):

	body = """<!DOCTYPE html>
<html lang="ja">
<head>
	<meta charset="utf-8">
	<title>Search</title>
</head>
<body>
	<h1>Search Page</h1>
	<p>以下はリクエストされたクエリです</p>
	<ul>
"""

	for label, detail in request.query.items():
		label = html.escape(label)
		detail = html.escape(' '.join(detail))
		body += f'\t\t<li>{label}: {detail}</li>\n'

	body += """\t</ul>
</body>
</html>
"""

	return body
```

ポイント:
- `"""`の直後に`<!DOCTYPE html>`を書く
- HTML内のインデントは`\t`ではなく、実際のタブ文字で書く
- Pythonコード自体のインデントを排除

### 方法2: textwrap.dedent()を使う

```python
from textwrap import dedent

@route('/search')
def	handle_search(request: Request):

	body = dedent("""
		<!DOCTYPE html>
		<html lang="ja">
		<head>
			<meta charset="utf-8">
			<title>Search</title>
		</head>
		<body>
			<h1>Search Page</h1>
			<p>以下はリクエストされたクエリです</p>
			<ul>
	""").lstrip()

	for label, detail in request.query.items():
		label = html.escape(label)
		detail = html.escape(' '.join(detail))
		body += f'\t\t\t<li>{label}: {detail}</li>\n'

	body += dedent("""
			</ul>
		</body>
		</html>
	""").lstrip()

	return body
```

`dedent()`は、文字列全体から共通のインデントを削除してくれます。

### 方法3: リストとjoinを使う

```python
@route('/search')
def	handle_search(request: Request):

	lines = [
		'<!DOCTYPE html>',
		'<html lang="ja">',
		'<head>',
		'\t<meta charset="utf-8">',
		'\t<title>Search</title>',
		'</head>',
		'<body>',
		'\t<h1>Search Page</h1>',
		'\t<p>以下はリクエストされたクエリです</p>',
		'\t<ul>',
	]

	for label, detail in request.query.items():
		label = html.escape(label)
		detail = html.escape(' '.join(detail))
		lines.append(f'\t\t<li>{label}: {detail}</li>')

	lines.extend([
		'\t</ul>',
		'</body>',
		'</html>',
	])

	return '\n'.join(lines)
```

この方法は、各行を明示的にリストで管理するため、インデントが正確に制御できます。

## おまけ: `join()`メソッドの復習

`join()`は文字列メソッドで、リストやタプルの要素を1つの文字列に結合します。

```python
# 基本構文
'区切り文字'.join(リスト)

# 例
words = ['apple', 'banana', 'orange']
result = ', '.join(words)
print(result)  # 'apple, banana, orange'

# parse_qs()の結果はリスト
query = {'q': ['python'], 'greetings': ['hello', 'world']}
# ['hello', 'world']を結合
' '.join(['hello', 'world'])  # 'hello world'
```

## セキュリティ: XSS対策

クエリパラメータはユーザー入力なので、**必ず`html.escape()`でエスケープ**してください。

```python
for label, detail in request.query.items():
	label = html.escape(label)
	detail = html.escape(' '.join(detail))  # リストなのでjoinしてからエスケープ
	body += f'\t\t<li>{label}: {detail}</li>\n'
```

これにより、`<script>`タグなどの悪意あるコードがHTMLとして解釈されるのを防げます。
