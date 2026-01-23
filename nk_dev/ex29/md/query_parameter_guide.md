# クエリパラメータ機能の追加ガイド

## 概要

URLのクエリパラメータ（例: `/search?q=python&page=2`）を処理する機能を追加する。

## 必要な変更箇所

### 1. インポートの追加

```python
from urllib.parse import urlparse, parse_qs
```

### 2. Requestクラスの拡張

クエリパラメータを保持するための属性を追加する。

```python
class Request:
    def __init__(self):
        self.method = None
        self.path = None          # クエリを除いたパス（例: /search）
        self.version = None
        self.query_string = None  # 生のクエリ文字列（例: q=python&page=2）
        self.query = {}           # パース済みクエリ（例: {'q': ['python'], 'page': ['2']}）
```

### 3. parse_http関数の修正

パスからクエリパラメータを分離する処理を追加する。

```python
def parse_http(http_line, request_obj):
    parts = http_line.split()
    if len(parts) != 3:
        return False

    request_obj.method = parts[0]
    request_obj.version = parts[2]

    # URLをパースしてパスとクエリを分離
    parsed = urlparse(parts[1])
    request_obj.path = parsed.path           # /search
    request_obj.query_string = parsed.query  # q=python&page=2
    request_obj.query = parse_qs(parsed.query)  # {'q': ['python'], 'page': ['2']}

    return True
```

### 4. クエリパラメータを使うハンドラーの例

```python
@route('/search')
def handle_search(request):
    # クエリパラメータを取得（デフォルト値付き）
    q = request.query.get('q', [''])[0]
    page = request.query.get('page', ['1'])[0]

    q = html.escape(q)
    page = html.escape(page)

    body = create_html(
        title='検索結果',
        h1=f'「{q}」の検索結果',
        content=f'''
        <p>検索キーワード: {q}</p>
        <p>ページ: {page}</p>
        <p>（これはダミーページです）</p>
        '''
    )
    return body
```

### 5. handle_client関数の修正

ハンドラーにrequestオブジェクトを渡すように変更する。

**変更前:**
```python
param = matched.groupdict()
response_obj.body = handler(**param)
```

**変更後:**
```python
param = matched.groupdict()
param['request'] = request_obj  # requestオブジェクトを追加
response_obj.body = handler(**param)
```

### 6. 既存ハンドラーの修正

既存のハンドラーも`request`引数を受け取れるように修正する。

```python
@route('/user/<user_id>')
def handle_user(user_id, request):
    # requestは使わなくてもOK（将来の拡張用）
    user_id = html.escape(user_id)
    # ... 以下同じ
```

または、`**kwargs`を使って後方互換性を保つ方法もある：

```python
@route('/user/<user_id>')
def handle_user(user_id, **kwargs):
    # kwargsにrequestが含まれる
    request = kwargs.get('request')
    # ...
```

## parse_qsの動作

`parse_qs`は同じキーの複数の値をリストとして返す：

| URL | parse_qsの結果 |
|-----|---------------|
| `?q=python` | `{'q': ['python']}` |
| `?q=python&page=2` | `{'q': ['python'], 'page': ['2']}` |
| `?tag=a&tag=b` | `{'tag': ['a', 'b']}` |

値は常にリストなので、単一の値を取得するには `[0]` でアクセスする。

## 実装の流れ

1. `urllib.parse` をインポート
2. `Request`クラスに `query_string` と `query` 属性を追加
3. `parse_http`関数でURLをパースしてクエリを分離
4. `handle_client`関数でハンドラーに`request`を渡す
5. 検索用ハンドラー `/search` を新規作成
6. 既存ハンドラーを必要に応じて修正

## テスト用URL例

- `http://127.0.0.1:8080/search?q=python`
- `http://127.0.0.1:8080/search?q=hello&page=3`
- `http://127.0.0.1:8080/user/123?debug=true`（動的パス + クエリ）
