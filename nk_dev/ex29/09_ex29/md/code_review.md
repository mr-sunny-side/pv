# HTTPサーバー実装 - コードレビュー

## プロジェクト概要

GET、POST、multipart/form-data（ファイルアップロード）に対応したHTTPサーバーの実装。マルチスレッド対応で複数のクライアントからの同時接続を処理可能。

## アーキテクチャ

### ファイル構成
- `09_ex29.py` - メインサーバー、スレッド管理、エラーハンドリング
- `http.py` - HTTPリクエストの解析とパース処理
- `route.py` - ルーティング、レスポンス生成、静的ファイル配信
- `error.py` - HTTPエラーレスポンスの生成
- `config.py` - 設定値とロギング設定

---

## ✅ 良い点（Strengths）

### 1. **適切なモジュール分割**
各ファイルが明確な責任を持ち、関心の分離ができている。
- HTTPプロトコル処理（`http.py`）
- ルーティングロジック（`route.py`）
- エラーハンドリング（`error.py`）

### 2. **マルチスレッド対応**
```python
client_thread = threading.Thread(
    target=handle_client,
    args=(client_socket, client_address),
    daemon=True
)
```
複数のクライアントを同時に処理可能。`daemon=True`により、メインスレッド終了時に自動的にクリーンアップされる。

### 3. **包括的なエラーハンドリング**
```python
except ValueError as e:
    logging.exception(f'ValueError handle_client:')
except socket.timeout:
    logging.warning('handle_client: Client timeout', exc_info=True)
except ConnectionError as e:
    logging.exception('handle_client: Client connection error')
except Exception as e:
    logging.exception(f'Exception handle_client:')
```
- 各エラータイプに対して適切な処理
- `logging.exception()`でスタックトレースを出力
- ユーザーに適切なHTTPステータスコードを返す

### 4. **セキュリティ対策**

#### パストラバーサル攻撃への対策
```python
if not str(file_path).startswith(str(STATIC_DIR.resolve())):
    logging.warning('static_search: Invalid path')
    return None
```

#### HTMLインジェクション対策
```python
label = html.escape(label)
detail = html.escape(detail)
```

### 5. **複数のContent-Typeサポート**
- `application/x-www-form-urlencoded` - 通常のPOST
- `multipart/form-data` - ファイルアップロード
- 静的ファイル配信（MIME type自動判定）

### 6. **適切なロギング**
```python
logging.debug('get_request: found header end')
logging.info('===== Request Details =====')
logging.error('get_request: Cannot parse http request')
```
デバッグ、情報、エラーの各レベルで適切にログ出力。

### 7. **リソース管理**
```python
finally:
    client_socket.close()
```
`finally`ブロックで確実にソケットをクローズ。

---

## 📚 学習ポイント（Learning Points）

### 1. **HTTPプロトコルの理解**

#### リクエストの構造
```
POST /path HTTP/1.1\r\n
Header1: value1\r\n
Header2: value2\r\n
\r\n
body data...
```
- ヘッダーとボディは`\r\n\r\n`で区切られる
- 各ヘッダー行は`\r\n`で区切られる

#### multipart/form-dataの構造
```
------boundary123\r\n
Content-Disposition: form-data; name="field1"\r\n
\r\n
value1\r\n
------boundary123\r\n
Content-Disposition: form-data; name="file"; filename="test.txt"\r\n
Content-Type: text/plain\r\n
\r\n
[binary data]\r\n
------boundary123--
```

### 2. **bytes型と文字列型の違い**

#### 問題が発生した箇所
```python
# http.py:48
request_obj.body[matched.group(1)] = line[1]  # bytes型
```

#### 対処方法
```python
# print_request関数で型チェック
if isinstance(detail, bytes):
    logging.info(f'\t{label}: len={len(detail)}')
    continue
```

**学習ポイント:**
- ネットワーク通信はbytes型で行われる
- テキストデータは適切なタイミングでデコードが必要
- バイナリデータ（画像、動画など）はbytes型のまま扱う

### 3. **エラーデバッグの方法**

#### 改善前
```python
except Exception as e:
    logging.error(e)  # エラーメッセージのみ
```

#### 改善後
```python
except Exception as e:
    logging.exception('Exception handle_client:')  # スタックトレース付き
```

**学習ポイント:**
- `logging.exception()`はスタックトレースを自動出力
- `exc_info=True`で他のログレベルでもスタックトレース出力可能
- エラーの発生箇所と行番号が特定できる

### 4. **型エラーのデバッグ**

#### エラーメッセージ
```
TypeError: sequence item 0: expected str instance, int found
```

#### 原因
```python
detail = ','.join(detail)  # detailがintを含むリストの場合エラー
```

#### 対策
```python
# 型を確認してから処理
if isinstance(detail, list):
    detail = ','.join(str(d) for d in detail)
```

---

## 🔧 改善の余地（Areas for Improvement）

### 1. **型安全性の向上**

#### 現在の問題
[http.py:146](http.py#L146)と[route.py:167](route.py#L167)で以下の前提がある：
```python
detail = ','.join(detail)  # detailがstr型のリストであることを前提
```

#### 推奨される改善
```python
# 型を確認してから処理
if isinstance(detail, list):
    detail = ','.join(str(item) for item in detail)
elif isinstance(detail, bytes):
    detail = f'<binary data, {len(detail)} bytes>'
else:
    detail = str(detail)
```

### 2. **Content-Lengthの型の一貫性**

#### 現在の実装
```python
# http.py:93 - 文字列として保存
request_obj.length = header.split(':')[1].strip()

# http.py:102 - 使用時にint変換
buffer = client_socket.recv(int(request_obj.length) - len(body_part))
```

#### 推奨される改善
最初からint型で保存するか、型ヒントを使用して明確化する：
```python
# Requestクラスで型ヒントを追加
class Request:
    def __init__(self):
        self.length: int | None = None
        # または
        self.length: Optional[int] = None
```

### 3. **エラーメッセージの改善**

#### 現在
```python
logging.error('get_request: Cannot parse http request')
```

#### 推奨
```python
logging.error(f'get_request: Cannot parse http request: {http_line}')
```
デバッグ時に問題のあるデータを確認できる。

### 4. **マジックナンバーの定数化**

#### 現在
```python
boundary_start = header.find('boundary=')
request_obj.boundary = header[boundary_start + len('boundary='):]
```

#### 推奨
```python
BOUNDARY_PREFIX = 'boundary='
boundary_start = header.find(BOUNDARY_PREFIX)
request_obj.boundary = header[boundary_start + len(BOUNDARY_PREFIX):]
```

### 5. **get_form_data関数の戻り値**

#### 現在
```python
def get_form_data(body_part: bytes, request_obj: Request) -> int:
    # ...処理...
    # 戻り値がない
```

#### 推奨
成功/失敗を明確に返すか、戻り値の型を`None`にする：
```python
def get_form_data(body_part: bytes, request_obj: Request) -> None:
    # または
def get_form_data(body_part: bytes, request_obj: Request) -> bool:
    # 処理...
    return True  # 成功時
```

---

## 🔒 セキュリティ（Security）

### 実装済みの対策

#### 1. パストラバーサル攻撃の防止
```python
if not str(file_path).startswith(str(STATIC_DIR.resolve())):
    return None
```
`../../../etc/passwd`のようなアクセスを防ぐ。

#### 2. HTMLインジェクション対策
```python
label = html.escape(label)
detail = html.escape(detail)
```
`<script>alert('XSS')</script>`のような攻撃を防ぐ。

#### 3. タイムアウト設定
```python
client_socket.settimeout(config.TIMEOUT_INT)
```
スローロリス攻撃などの長時間接続を防ぐ。

#### 4. リクエストサイズの制限
```python
if config.MAX_READ < len(buffer):
    logging.error('get_request: Request header is too long')
    return
```
巨大なリクエストによるメモリ枯渇を防ぐ。

### 追加で検討すべき対策

#### 1. レート制限
同一IPからの大量リクエストを制限する：
```python
# 例: IPアドレスごとのリクエスト数を追跡
request_counts = {}  # {ip: (count, timestamp)}
```

#### 2. ファイルアップロードのサイズ制限
```python
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
if request_obj.length > MAX_UPLOAD_SIZE:
    return handle_413()  # 413 Payload Too Large
```

#### 3. ファイルタイプの検証
```python
ALLOWED_EXTENSIONS = {'.txt', '.pdf', '.jpg', '.png'}
file_ext = os.path.splitext(filename)[1].lower()
if file_ext not in ALLOWED_EXTENSIONS:
    return handle_400()
```

#### 4. CSRFトークン
POST/PUT/DELETEリクエストでトークンを検証する。

---

## 🎯 次のステップ（Next Steps）

### 基礎的な機能拡張

#### 1. ファイルアップロードの保存
```python
def save_uploaded_file(file_data: bytes, filename: str) -> str:
    upload_dir = Path('uploads')
    upload_dir.mkdir(exist_ok=True)

    # ファイル名のサニタイズ
    safe_filename = secure_filename(filename)
    file_path = upload_dir / safe_filename

    file_path.write_bytes(file_data)
    return str(file_path)
```

#### 2. 追加のHTTPメソッド
- PUT - リソースの更新
- DELETE - リソースの削除
- PATCH - リソースの部分更新

#### 3. クエリパラメータの高度な処理
```python
# /search?tags=python,web&sort=date&limit=10
tags = request_obj.query.get('tags', [''])[0].split(',')
sort = request_obj.query.get('sort', [''])[0]
limit = int(request_obj.query.get('limit', ['10'])[0])
```

### 中級的な機能拡張

#### 1. セッション管理
```python
import uuid
import time

sessions = {}  # {session_id: {user_id, expires, data}}

def create_session(user_id: str) -> str:
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        'user_id': user_id,
        'expires': time.time() + 3600,  # 1時間
        'data': {}
    }
    return session_id
```

#### 2. Cookie処理
```python
def parse_cookies(cookie_header: str) -> dict:
    cookies = {}
    for item in cookie_header.split(';'):
        if '=' in item:
            key, value = item.strip().split('=', 1)
            cookies[key] = value
    return cookies
```

#### 3. JSONレスポンス
```python
import json

def handle_api_endpoint(**kwargs) -> Response:
    data = {
        'status': 'success',
        'data': {'user_id': 123, 'name': 'Alice'}
    }
    body = json.dumps(data, ensure_ascii=False)

    return Response(
        status=200,
        reason='OK',
        headers={'Content-Type': 'application/json; charset=utf-8'},
        body=body
    )
```

### 上級的な機能拡張

#### 1. HTTPSサポート
```python
import ssl

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain('server.crt', 'server.key')

secure_socket = context.wrap_socket(server_socket, server_side=True)
```

#### 2. データベース連携
```python
import sqlite3

def get_user(user_id: int):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user
```

#### 3. テンプレートエンジン
```python
from jinja2 import Template

template = Template('''
<!DOCTYPE html>
<html>
<head><title>{{ title }}</title></head>
<body>
    <h1>{{ heading }}</h1>
    {% for item in items %}
        <li>{{ item }}</li>
    {% endfor %}
</body>
</html>
''')

body = template.render(
    title='My Page',
    heading='Welcome',
    items=['Item 1', 'Item 2', 'Item 3']
)
```

#### 4. WebSocket対応
リアルタイム通信のサポート。

#### 5. ミドルウェアパターン
```python
def logging_middleware(handler):
    def wrapper(**kwargs):
        start = time.time()
        response = handler(**kwargs)
        duration = time.time() - start
        logging.info(f'Request processed in {duration:.3f}s')
        return response
    return wrapper

@route('/api/data')
@logging_middleware
def handle_api_data(**kwargs):
    # ...
```

---

## 📊 パフォーマンス最適化

### 1. コネクションプール
データベース接続を再利用する。

### 2. キャッシング
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_static_file(path: str):
    # ファイルを読み込んでキャッシュ
```

### 3. 非同期処理
```python
import asyncio

async def handle_client_async(reader, writer):
    # 非同期でリクエストを処理
```

### 4. gzip圧縮
```python
import gzip

if 'gzip' in request_obj.headers.get('Accept-Encoding', ''):
    body = gzip.compress(body.encode('utf-8'))
    headers['Content-Encoding'] = 'gzip'
```

---

## 🧪 テストの追加

### 単体テスト例
```python
import unittest

class TestHTTPParser(unittest.TestCase):
    def test_parse_http(self):
        request_obj = Request()
        result = parse_http('GET /path HTTP/1.1', request_obj)

        self.assertTrue(result)
        self.assertEqual(request_obj.method, 'GET')
        self.assertEqual(request_obj.path, '/path')
        self.assertEqual(request_obj.version, 'HTTP/1.1')

    def test_parse_query_string(self):
        request_obj = Request()
        parse_http('GET /search?q=python&limit=10 HTTP/1.1', request_obj)

        self.assertEqual(request_obj.query['q'], ['python'])
        self.assertEqual(request_obj.query['limit'], ['10'])
```

### 統合テスト例
```python
import requests

def test_post_form_data():
    response = requests.post(
        'http://localhost:8080/submit',
        data={'name': 'Alice', 'age': '30'}
    )
    assert response.status_code == 200
    assert 'Alice' in response.text
```

---

## 💡 総評

### 成果
- **HTTPプロトコルの深い理解**: リクエスト/レスポンスの構造、各種Content-Type
- **実践的なエラーハンドリング**: デバッグ方法、ロギング戦略
- **型システムの重要性**: bytes vs str、型チェックの必要性
- **セキュリティ意識**: 基本的な攻撃への対策
- **マルチスレッド処理**: 並行処理の基礎

### 学習の軌跡
このプロジェクトを通じて、以下のような問題解決のプロセスを経験：

1. **問題発見**: `TypeError: sequence item 0: expected str instance, int found`
2. **調査**: `logging.exception()`でスタックトレースを取得
3. **原因特定**: bytes型とstr型の混在、型チェック不足
4. **対策実装**: `isinstance()`で型を確認してから処理

このような実践的なデバッグ経験は、プログラミングスキルの向上に非常に価値があります。

### 次の学習目標
1. **フレームワークの理解**: Flask/FastAPIなどのコードを読んで比較
2. **プロトコルの深掘り**: HTTP/2、WebSocket、gRPC
3. **スケーラビリティ**: 負荷分散、水平スケーリング
4. **DevOps**: Docker化、CI/CD、モニタリング

---

## 📖 参考資料

### 公式ドキュメント
- [RFC 7230 - HTTP/1.1 Message Syntax and Routing](https://www.rfc-editor.org/rfc/rfc7230)
- [RFC 7578 - multipart/form-data](https://www.rfc-editor.org/rfc/rfc7578)
- [Python socket documentation](https://docs.python.org/3/library/socket.html)
- [Python threading documentation](https://docs.python.org/3/library/threading.html)

### 推奨書籍
- "HTTP: The Definitive Guide" - O'Reilly
- "Computer Networking: A Top-Down Approach" - Kurose & Ross

### オンラインリソース
- [MDN Web Docs - HTTP](https://developer.mozilla.org/en-US/docs/Web/HTTP)
- [Real Python - Socket Programming](https://realpython.com/python-sockets/)

---

**作成日**: 2026-02-05
**対象**: HTTPサーバー実装（ex29/09_ex29）
**レビュアー**: Claude Code
