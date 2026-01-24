# re07_ex29.py ロジックエラーのフィードバック

日付: 2026-01-25

## 概要
re07_ex29.pyに複数のロジックエラーが見つかりました。以下、各エラーの詳細と修正方法を説明します。

---

## エラー1: タイポ - Content-Lengthヘッダー（重大度: 低）

**場所**: [re07_ex29.py:112](../re07_ex29.py#L112)

**問題**:
```python
'COntent-Length': length
```

**詳細**:
`Content-Length` の `O` が大文字になっています。HTTPヘッダーは大文字小文字を区別しませんが、標準的な表記は `Content-Length` です。他の箇所（128行目など）では正しく記述されているため、単純なタイポと思われます。

**修正**:
```python
'Content-Length': length
```

---

## エラー2: Responseクラスのデフォルト引数に可変オブジェクト（重大度: 高）

**場所**: [re07_ex29.py:46](../re07_ex29.py#L46)

**問題**:
```python
def	__init__(self, status=200, reason='OK', headers={}, body=''):
```

**詳細**:
Pythonでは、デフォルト引数として可変オブジェクト（リスト、辞書など）を使用すると、そのオブジェクトは関数定義時に一度だけ作成され、すべての呼び出しで共有されます。これにより、異なるResponseインスタンス間でheadersが共有される危険性があります。

**具体例**:
```python
# 以下のようなコードでバグが発生する可能性があります
response1 = Response()
response2 = Response()
# response1とresponse2が同じheaders辞書を共有してしまう
```

**修正**:
```python
def	__init__(self, status=200, reason='OK', headers=None, body=''):
	self.status = status
	self.reason = reason
	self.headers = headers if headers is not None else {}
	self.body = body

	if 'Content-Type' not in self.headers:
		self.headers['Content-Type'] = 'text/html; charset=utf-8'
	if 'Connection' not in self.headers:
		self.headers['Connection'] = 'close'
```

---

## エラー3: file_path.resolve()の戻り値を使用していない（重大度: 中）

**場所**: [re07_ex29.py:191](../re07_ex29.py#L191)

**問題**:
```python
file_path = path.lstrip()
file_path = STATIC_DIR / file_path
file_path.resolve()  # 戻り値を使っていない
```

**詳細**:
`Path.resolve()` メソッドは、絶対パスに変換した新しいPathオブジェクトを返しますが、元のオブジェクトを変更しません。そのため、195行目のセキュリティチェックが正しく機能しない可能性があります。

**修正**:
```python
file_path = path.lstrip('/')
file_path = STATIC_DIR / file_path
file_path = file_path.resolve()  # 戻り値を代入する
```

**注意**: `path.lstrip()` ではなく `path.lstrip('/')` を使うべきです。`lstrip()` 引数なしだと、先頭の空白文字を削除しますが、パスの先頭の `/` を削除したい場合は明示的に `/` を指定すべきです。

---

## エラー4: ルーティングのロジックエラー（重大度: 最高）

**場所**: [re07_ex29.py:285-292](../re07_ex29.py#L285-L292)

**問題**:
```python
for pattern, handler in routes:
	matched = pattern.match(request_obj.path)
	param = matched.groupdict()  # matchedがNoneの可能性がある
	param['request_obj'] = request_obj
	response_obj = handler(**param)

response_bytes = response_obj.to_bytes()  # response_objが未定義の可能性がある
client_socket.sendall(response_bytes)
```

**詳細**:
このコードには3つの重大な問題があります：

1. **matchedがNoneの場合のチェックがない**: パターンがマッチしない場合、`matched` は `None` になり、287行目で `AttributeError: 'NoneType' object has no attribute 'groupdict'` が発生します。

2. **マッチした後もループが継続する**: マッチしても `break` がないため、すべてのルートパターンをチェックし続けます。これは非効率で、意図しない動作を引き起こす可能性があります。

3. **どのルートにもマッチしなかった場合の処理がない**: すべてのパターンがマッチしなかった場合、`response_obj` は未定義のまま291行目で使用され、`NameError` が発生します。

**修正**:
```python
# 基本htmlとパスのルーティング
# /, /about, /time, /search
response_obj = None
for pattern, handler in routes:
	matched = pattern.match(request_obj.path)
	if matched:
		param = matched.groupdict()
		param['request_obj'] = request_obj
		response_obj = handler(**param)
		break  # マッチしたらループを抜ける

# どのルートにもマッチしなかった場合は404を返す
if not response_obj:
	body = create_html(
		title='404 Not Found',
		h1='404 Not Found',
		content='\t<p>指定されたページは見つかりませんでした</p>'
	)
	response_obj = Response(
		status=404,
		reason='Not Found',
		body=body
	)

response_bytes = response_obj.to_bytes()
client_socket.sendall(response_bytes)
```

---

## エラー5: ValueErrorに情報が含まれていない（重大度: 低）

**場所**: [re07_ex29.py:273](../re07_ex29.py#L273)

**問題**:
```python
if not parse_http(request_line[0], request_obj):
	raise ValueError
```

**詳細**:
`raise ValueError` だけでは、エラーメッセージが含まれないため、294行目の例外ハンドラで `{e}` を表示しても何も表示されません。これによりデバッグが困難になります。

**修正**:
```python
if not parse_http(request_line[0], request_obj):
	raise ValueError(f'Invalid HTTP request line: {request_line[0]}')
```

---

## エラーの優先順位

修正すべき優先順位（高→低）：

1. **エラー4**: ルーティングのロジックエラー（最優先）
   - 現在、すべてのリクエストで `AttributeError` が発生しています

2. **エラー3**: file_path.resolve()の戻り値を使用していない
   - セキュリティチェックが正しく機能しない可能性があります

3. **エラー2**: Responseクラスのデフォルト引数
   - 潜在的なバグの原因になります

4. **エラー5**: ValueErrorのメッセージ
   - デバッグを容易にします

5. **エラー1**: タイポ
   - 動作には影響しませんが、一貫性のために修正すべきです

---

## 追加の改善提案

### 1. handle_search関数の引数処理

**場所**: [re07_ex29.py:157](../re07_ex29.py#L157)

`handle_search` は `request_obj` を引数として受け取りますが、他のハンドラ（`handle_html`, `handle_about`, `handle_user`）は受け取りません。ルーティングロジック（288行目）では常に `request_obj` を渡しているため、受け取らないハンドラでエラーが発生する可能性があります。

**対策**:
- すべてのハンドラで `**kwargs` を受け取り、不要な引数を無視する
- または、ルーティングロジックで関数のシグネチャをチェックし、必要な引数のみを渡す

### 2. エラーハンドリングの改善

現在、すべての例外を `ValueError` として扱っていますが、より具体的なエラーハンドリングを追加することで、デバッグが容易になります。

```python
except ValueError as e:
	print(f'ValueError handle_client: {e}')
	# 400 Bad Requestを返す
	error_response = Response(
		status=400,
		reason='Bad Request',
		body='Invalid request'
	)
	client_socket.sendall(error_response.to_bytes())
except Exception as e:
	print(f'Error handle_client: {e}')
	# 500 Internal Server Errorを返す
	error_response = Response(
		status=500,
		reason='Internal Server Error',
		body='Server error'
	)
	client_socket.sendall(error_response.to_bytes())
```

---

## まとめ

現在のコードでは、特に**エラー4のルーティングロジック**が原因で、すべてのリクエストで例外が発生しています。この問題を最優先で修正する必要があります。

その他のエラーも、セキュリティやコードの品質に影響するため、順次修正することをお勧めします。
