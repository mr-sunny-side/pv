# HTTPサーバー改善実装ガイド

## 新要素の実装リファレンス

次回の実装で追加すべき新機能・改善点のコード集です。

---

## 1. タイムアウト設定

### 実装箇所: `08_ex29.py:50` (handle_client関数)

```python
def handle_client(client_socket, client_address):
    global client_count
    try:
        # タイムアウト設定を追加（30秒）
        client_socket.settimeout(30.0)

        with lock:
            client_count += 1
            client_id = client_count
        # 以下既存のコード
```

**効果**: クライアントが応答しない場合にスレッドが無限にブロックされるのを防ぐ

---

## 2. リクエストサイズ制限（DoS対策）

### 2-1. ヘッダーサイズ制限

**実装箇所**: `http.py:35` (get_request関数)

```python
def get_request(client_socket, request_obj) -> int:
    ## headerの取得と分離
    # 最大ヘッダーサイズを定数化
    MAX_HEADER_SIZE = 8192  # 8KB

    buffer = b''
    while b'\r\n\r\n' not in buffer:
        # サイズチェックを追加
        if len(buffer) > MAX_HEADER_SIZE:
            print('ERROR get_request: Header size exceeds limit')
            return 1

        buffer += client_socket.recv(4096)
        if not buffer:
            print('Warning handle_client: Request is empty')
            return -1

    # 以下既存のコード
```

### 2-2. ボディサイズ制限

**実装箇所**: `http.py:70` (Content-Length取得後)

```python
    # body長を取得できなかったらエラー
    if not request_obj.length:
        print('ERROR get_header: Cannot find Content-Length in POST method')
        return 1

    # ボディサイズ制限を追加
    MAX_BODY_SIZE = 10 * 1024 * 1024  # 10MB
    if request_obj.length > MAX_BODY_SIZE:
        print(f'ERROR get_request: Body size {request_obj.length} exceeds limit {MAX_BODY_SIZE}')
        return 1

    # content-lengthの値から残りのbodyを読み込み
    buffer = client_socket.recv(request_obj.length - len(body_parts))
```

**効果**: 悪意のあるクライアントが巨大なデータを送信してメモリを枯渇させるのを防ぐ

---

## 3. ロギングの標準化

### 実装箇所: 全ファイル共通

**ファイル冒頭に追加**:

```python
import logging

# ロガー設定（各ファイルに追加）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

**使用例**:

```python
# 従来
print('ERROR parse_http/get_header: http_line')

# 改善後
logger.error('parse_http: Invalid HTTP request line')
```

```python
# 従来
print('Warning static_search: Invalid path')

# 改善後
logger.warning('static_search: Path traversal attempt detected')
```

```python
# 従来
print(f'ValueError handle_client: {e}')

# 改善後
logger.error(f'handle_client: ValueError occurred - {e}')
```

**ログレベルの使い分け**:
- `logger.debug()`: デバッグ情報（開発時のみ）
- `logger.info()`: 通常の動作情報（接続検出など）
- `logger.warning()`: 警告（不正なパスなど）
- `logger.error()`: エラー（リクエストパースエラーなど）
- `logger.critical()`: 致命的エラー（サーバー起動失敗など）

---

## 4. ヘッダーインジェクション対策

### 実装箇所: `route.py:22` (Response.to_bytes メソッド)

```python
def to_bytes(self):
    response = f'HTTP/1.1 {self.status} {self.reason}\r\n'

    for label, detail in self.headers.items():
        # 改行文字を除去してヘッダーインジェクションを防ぐ
        label = str(label).replace('\r', '').replace('\n', '')
        detail = str(detail).replace('\r', '').replace('\n', '')
        response += f'{label}: {detail}\r\n'

    response += '\r\n'
    response = response.encode('utf-8', errors='replace')

    # 以下既存のコード
```

**効果**: ヘッダー値に改行文字が含まれていた場合のインジェクション攻撃を防ぐ

---

## 5. ファイル読み込みのエラーハンドリング

### 実装箇所: `route.py:65` (static_search関数)

```python
    # bodyの読み込み（エラーハンドリングを追加）
    try:
        if mime_types.startswith('text/') or \
            mime_types in ['application/javascript', 'application/json']:
            body = file_path.read_text('utf-8')
            length = len(body.encode('utf-8', errors='replace'))
        else:
            body = file_path.read_bytes()
            length = len(body)
    except IOError as e:
        logger.error(f'static_search: Failed to read file {file_path} - {e}')
        return None
    except Exception as e:
        logger.error(f'static_search: Unexpected error reading file {file_path} - {e}')
        return None

    return Response(
        status=200,
        reason='OK',
        headers={
            'Content-Type': mime_types,
            'Content-Length': length
        },
        body=body
    )
```

**効果**: ファイル読み込み時の権限エラーやディスク障害に対応

---

## 6. 設定の定数化

### 新規ファイル: `config.py`

```python
"""サーバー設定"""

# ネットワーク設定
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 8080
SOCKET_BACKLOG = 5

# タイムアウト設定
CLIENT_TIMEOUT = 30.0  # 秒

# バッファサイズ
RECV_BUFFER_SIZE = 4096

# リクエストサイズ制限
MAX_HEADER_SIZE = 8192          # 8KB
MAX_BODY_SIZE = 10 * 1024 * 1024  # 10MB

# スレッド設定
DAEMON_THREADS = True

# ログ設定
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
```

**使用例**（`08_ex29.py`で）:

```python
import config

def run_server(host=config.SERVER_HOST, port=config.SERVER_PORT):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(config.SOCKET_BACKLOG)
    # 以下既存のコード
```

---

## 7. 例外の詳細分類

### 実装箇所: `08_ex29.py:102` (handle_client関数)

```python
except ValueError as e:
    logger.error(f'handle_client: Bad request - {e}')
    response = b'HTTP/1.1 400 Bad Request\r\n'
    response += b'Content-Type: text/plain\r\n'
    response += b'Connection: close\r\n'
    response += b'\r\n'
    response += b'400 Bad Request\n'
    client_socket.sendall(response)

except socket.timeout:
    logger.warning(f'handle_client: Client timeout - {client_address}')
    response = b'HTTP/1.1 408 Request Timeout\r\n'
    response += b'Content-Type: text/plain\r\n'
    response += b'Connection: close\r\n'
    response += b'\r\n'
    response += b'408 Request Timeout\n'
    client_socket.sendall(response)

except ConnectionError as e:
    logger.warning(f'handle_client: Connection error - {e}')
    # クライアント切断なので応答不要

except Exception as e:
    logger.error(f'handle_client: Internal server error - {e}')
    response = b'HTTP/1.1 500 Internal Server Error\r\n'
    response += b'Content-Type: text/plain\r\n'
    response += b'Connection: close\r\n'
    response += b'\r\n'
    response += b'500 Internal Server Error\n'
    client_socket.sendall(response)

finally:
    client_socket.close()
```

**効果**: エラーの種類に応じた適切なHTTPステータスコードを返す

---

## 8. docstringの追加

### テンプレート

```python
def get_request(client_socket, request_obj) -> int:
    """
    HTTPリクエストをソケットから読み込み、Requestオブジェクトに格納する

    Args:
        client_socket (socket.socket): クライアントとの通信ソケット
        request_obj (Request): リクエスト情報を格納するRequestオブジェクト

    Returns:
        int: 処理結果
            0: 正常終了
            1: 不正なリクエスト（400エラー相当）
            -1: 接続切断

    Raises:
        socket.timeout: タイムアウト発生時
    """
    # 実装
```

```python
class Response:
    """HTTPレスポンスを表現するクラス

    Attributes:
        status (int): HTTPステータスコード (例: 200, 404, 500)
        reason (str): ステータスの説明 (例: 'OK', 'Not Found')
        headers (dict): レスポンスヘッダー
        body (str | bytes): レスポンスボディ
    """

    def __init__(self, status=200, reason='OK', headers=None, body=''):
        """
        Args:
            status (int): HTTPステータスコード
            reason (str): ステータス説明
            headers (dict, optional): カスタムヘッダー
            body (str | bytes): レスポンスボディ
        """
```

---

## 9. ユニットテスト例

### 新規ファイル: `tests/test_http.py`

```python
import unittest
from http import Request, parse_http

class TestHTTPParser(unittest.TestCase):

    def test_parse_http_valid_get(self):
        """正常なGETリクエストのパース"""
        request_obj = Request()
        http_line = "GET /index.html HTTP/1.1"
        result = parse_http(http_line, request_obj)

        self.assertTrue(result)
        self.assertEqual(request_obj.method, 'GET')
        self.assertEqual(request_obj.path, '/index.html')
        self.assertEqual(request_obj.version, 'HTTP/1.1')

    def test_parse_http_with_query(self):
        """クエリパラメータ付きリクエストのパース"""
        request_obj = Request()
        http_line = "GET /search?q=python&test=hello HTTP/1.1"
        result = parse_http(http_line, request_obj)

        self.assertTrue(result)
        self.assertEqual(request_obj.path, '/search')
        self.assertIn('q', request_obj.query)
        self.assertEqual(request_obj.query['q'], ['python'])

    def test_parse_http_invalid_format(self):
        """不正なフォーマットの処理"""
        request_obj = Request()
        http_line = "INVALID REQUEST"
        result = parse_http(http_line, request_obj)

        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
```

### 新規ファイル: `tests/test_route.py`

```python
import unittest
from route import Response

class TestResponse(unittest.TestCase):

    def test_response_to_bytes(self):
        """Responseオブジェクトのバイト変換"""
        response = Response(
            status=200,
            reason='OK',
            body='Hello World'
        )
        result = response.to_bytes()

        self.assertIn(b'HTTP/1.1 200 OK', result)
        self.assertIn(b'Hello World', result)

    def test_response_with_custom_headers(self):
        """カスタムヘッダーの処理"""
        response = Response(
            status=404,
            reason='Not Found',
            headers={'X-Custom-Header': 'test'},
            body='Not Found'
        )
        result = response.to_bytes()

        self.assertIn(b'X-Custom-Header: test', result)
        self.assertIn(b'404 Not Found', result)

if __name__ == '__main__':
    unittest.main()
```

**実行方法**:
```bash
python -m unittest discover tests
```

---

## 10. 環境変数による設定

### 実装箇所: `config.py`（既存のconfig.pyを拡張）

```python
import os

# 環境変数から設定を読み込む（デフォルト値を設定）
SERVER_HOST = os.getenv('SERVER_HOST', '127.0.0.1')
SERVER_PORT = int(os.getenv('SERVER_PORT', '8080'))
CLIENT_TIMEOUT = float(os.getenv('CLIENT_TIMEOUT', '30.0'))

MAX_HEADER_SIZE = int(os.getenv('MAX_HEADER_SIZE', '8192'))
MAX_BODY_SIZE = int(os.getenv('MAX_BODY_SIZE', str(10 * 1024 * 1024)))

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
```

**使用方法**:
```bash
# 環境変数で設定を変更
export SERVER_PORT=9000
export LOG_LEVEL=DEBUG
python 08_ex29.py
```

---

## 実装優先度

### 優先度: 高（セキュリティ・安定性）
1. ✅ タイムアウト設定（§1）
2. ✅ リクエストサイズ制限（§2）
3. ✅ ヘッダーインジェクション対策（§4）
4. ✅ ファイル読み込みエラーハンドリング（§5）

### 優先度: 中（保守性）
5. ✅ ロギングの標準化（§3）
6. ✅ 例外の詳細分類（§7）
7. ✅ 設定の定数化（§6）

### 優先度: 低（品質向上）
8. ✅ docstringの追加（§8）
9. ✅ ユニットテスト（§9）
10. ✅ 環境変数設定（§10）

---

## 実装時の注意点

### インポート順序
```python
# 標準ライブラリ
import sys
import socket
import threading
import logging

# サードパーティライブラリ
# (このプロジェクトでは使用していない)

# ローカルモジュール
import config
from http import get_request, print_request, Request
from route import handle_post_method, handle_404, static_search, search_route
```

### マジックナンバーの撲滅
```python
# ❌ 悪い例
buffer += client_socket.recv(4096)

# ✅ 良い例
buffer += client_socket.recv(config.RECV_BUFFER_SIZE)
```

### エラーメッセージの一貫性
```python
# 形式: "関数名: エラー内容"
logger.error('get_request: Header size exceeds limit')
logger.warning('static_search: Path traversal attempt detected')
logger.info('run_server: Server started successfully')
```

---

## 実装チェックリスト

実装時に確認すべき項目：

- [ ] タイムアウトを設定したか
- [ ] サイズ制限を実装したか
- [ ] print文をloggerに置き換えたか
- [ ] マジックナンバーを定数化したか
- [ ] エラーハンドリングを追加したか
- [ ] docstringを書いたか
- [ ] セキュリティチェックを実装したか
- [ ] テストを書いたか

---

*この実装ガイドは、既存コードの修正ではなく、新規追加要素のリファレンスです。*
*実装の際は優先度の高いものから段階的に追加してください。*
