# multipart/form-data エラーハンドリング戦略

## 問題：ファイル数とサイズの制限

### 脅威モデル

| 攻撃手法 | 影響 | 対策 |
|---------|------|------|
| 大量のファイル送信（1000個以上） | メモリ枯渇 | **ファイル数の制限** |
| 巨大ファイル送信（1GB以上） | メモリ/ディスク枯渇 | **ファイルサイズの制限** |
| Content-Length偽装 | バッファオーバーフロー | **実際の読み込みサイズの監視** |
| 無限ループ攻撃（終了マーカーなし） | CPU占有 | **タイムアウト設定** |

---

## 1. Content-Lengthを使った検証

### 1.1 基本的な流れ

```python
def get_request(client_socket, request_obj) -> int:
    # ... (ヘッダーの読み込み)

    # Content-Lengthを取得
    content_length = None
    for header in header_line[1:]:
        parts = header.split(':', 1)
        if len(parts) < 2:
            continue

        key = parts[0].strip()
        value = parts[1].strip()

        if key == 'Content-Length':
            content_length = int(value)
            request_obj.length = content_length
            break

    # Content-Lengthがない、または異常値の場合
    if content_length is None:
        logging.error('get_request: Content-Length not found')
        return -1

    if content_length <= 0:
        logging.error(f'get_request: Invalid Content-Length: {content_length}')
        return -1

    # 最大サイズチェック（例: 100MB）
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    if content_length > MAX_CONTENT_LENGTH:
        logging.error(f'get_request: Content-Length too large: {content_length}')
        return -1  # 413 Payload Too Large を返すべき
```

### 1.2 実際の読み込みサイズの監視

```python
def get_request(client_socket, request_obj) -> int:
    # ... (ヘッダー読み込み後)

    # 既に読み込んだボディ部分
    body_part = buffer[header_end + 4:]
    already_read = len(body_part)

    # 残りのボディを読み込む
    remaining = content_length - already_read

    # 安全のため、分割して読み込む
    CHUNK_SIZE = 8192  # 8KB
    total_read = already_read

    while total_read < content_length:
        chunk_size = min(CHUNK_SIZE, content_length - total_read)
        chunk = client_socket.recv(chunk_size)

        if not chunk:
            # 接続が切れた
            logging.error(f'get_request: Connection closed. Expected {content_length}, got {total_read}')
            return -1

        body_part += chunk
        total_read += len(chunk)

        # 念のため: Content-Lengthを超えて読み込まないようにする
        if total_read > content_length:
            logging.error(f'get_request: Read more than Content-Length: {total_read} > {content_length}')
            return -1

    logging.debug(f'get_request: Read {total_read} bytes (expected {content_length})')

    # Content-Typeに応じて処理を分岐
    # ...
```

---

## 2. ファイル数の制限

### 2.1 設定値の定義

[config.py](../config.py) に追加：

```python
# multipart/form-data の制限
MAX_FILES = 10                          # 最大ファイル数
MAX_FILE_SIZE = 10 * 1024 * 1024        # 1ファイルあたり10MB
MAX_TOTAL_SIZE = 100 * 1024 * 1024      # 全体で100MB
MAX_FIELD_SIZE = 1 * 1024 * 1024        # 通常フィールド1MB
```

### 2.2 パース処理での検証

```python
def parse_multipart(body_bytes: bytes, boundary: str, max_files: int = 10) -> dict | None:
    """
    multipart/form-dataをパースする（制限付き）

    Args:
        body_bytes: リクエストボディ全体（バイナリ）
        boundary: 境界文字列
        max_files: 最大ファイル数（デフォルト10）

    Returns:
        成功: {'fields': {...}, 'files': {...}}
        失敗: None
    """
    result_fields = {}  # 通常フィールド
    result_files = {}   # ファイル

    file_count = 0
    total_size = 0

    # 境界文字列の準備
    boundary_bytes = f'--{boundary}'.encode('utf-8')
    end_boundary_bytes = f'--{boundary}--'.encode('utf-8')

    # ボディを分割
    parts = body_bytes.split(boundary_bytes)

    for part in parts[1:]:  # 最初の要素は空
        if end_boundary_bytes in part:
            break

        # 空のパートをスキップ
        if len(part.strip()) == 0:
            continue

        # ヘッダーとデータを分離
        header_end = part.find(b'\r\n\r\n')
        if header_end == -1:
            logging.warning('parse_multipart: Invalid part (no header end)')
            continue

        headers = part[:header_end].decode('utf-8', errors='replace')
        data = part[header_end + 4:]

        # 末尾の\r\nを削除
        if data.endswith(b'\r\n'):
            data = data[:-2]

        # データサイズをチェック
        data_size = len(data)
        total_size += data_size

        # Content-Dispositionをパース
        name = None
        filename = None
        content_type = 'text/plain'

        for line in headers.split('\r\n'):
            if line.startswith('Content-Disposition:'):
                # name="field_name" を抽出
                if 'name="' in line:
                    start = line.find('name="') + 6
                    end = line.find('"', start)
                    name = line[start:end]

                # filename="file.jpg" を抽出
                if 'filename="' in line:
                    start = line.find('filename="') + 10
                    end = line.find('"', start)
                    filename = line[start:end]

            elif line.startswith('Content-Type:'):
                content_type = line.split(':', 1)[1].strip()

        if not name:
            logging.warning('parse_multipart: Part without name, skipping')
            continue

        # ファイルの場合
        if filename:
            # ファイル数制限チェック
            file_count += 1
            if file_count > max_files:
                logging.error(f'parse_multipart: Too many files (max {max_files})')
                return None  # エラー

            # 個別ファイルサイズチェック
            if data_size > config.MAX_FILE_SIZE:
                logging.error(f'parse_multipart: File too large: {data_size} bytes')
                return None

            result_files[name] = {
                'filename': filename,
                'content_type': content_type,
                'data': data,
                'size': data_size
            }
            logging.info(f'parse_multipart: File "{filename}" ({data_size} bytes)')

        # 通常フィールドの場合
        else:
            # フィールドサイズチェック
            if data_size > config.MAX_FIELD_SIZE:
                logging.error(f'parse_multipart: Field too large: {data_size} bytes')
                return None

            try:
                text_data = data.decode('utf-8')
                result_fields[name] = text_data
            except UnicodeDecodeError:
                logging.warning(f'parse_multipart: Cannot decode field "{name}"')
                result_fields[name] = data.decode('utf-8', errors='replace')

    # 全体サイズチェック
    if total_size > config.MAX_TOTAL_SIZE:
        logging.error(f'parse_multipart: Total size too large: {total_size} bytes')
        return None

    logging.info(f'parse_multipart: Parsed {len(result_fields)} fields, {file_count} files')

    return {
        'fields': result_fields,
        'files': result_files
    }
```

---

## 3. Requestクラスへの保存

### 3.1 Requestクラスの拡張

[http.py](../http.py) のRequestクラス：

```python
class Request:
    def __init__(self):
        self.method = None
        self.path = None
        self.version = None
        self.length = None
        self.query = {}
        self.body = {}           # 通常フィールド（dict）
        self.content_type = None  # Content-Type
        self.files = {}          # ファイル（dict）
```

### 3.2 パース結果の保存

```python
def get_request(client_socket, request_obj) -> int:
    # ... (ヘッダー読み込み、ボディ読み込み)

    # Content-Typeを取得
    content_type = None
    for header in header_line[1:]:
        if header.startswith('Content-Type:'):
            content_type = header.split(':', 1)[1].strip()
            request_obj.content_type = content_type
            break

    # multipart/form-dataの場合
    if content_type and 'multipart/form-data' in content_type:
        # boundaryを抽出
        boundary = extract_boundary(content_type)
        if not boundary:
            logging.error('get_request: Cannot extract boundary')
            return -1

        # パース実行
        parsed_data = parse_multipart(body_part, boundary, max_files=config.MAX_FILES)

        if parsed_data is None:
            # パースエラー（制限超過など）
            logging.error('get_request: Failed to parse multipart data')
            return -1

        # Requestオブジェクトに保存
        request_obj.body = parsed_data['fields']  # 通常フィールド
        request_obj.files = parsed_data['files']  # ファイル

        logging.info(f'get_request: Stored {len(request_obj.body)} fields, {len(request_obj.files)} files')

    else:
        # 従来のapplication/x-www-form-urlencoded
        body_part = body_part.decode('utf-8', errors='replace')
        request_obj.body = parse_qs(body_part)

    return 0
```

---

## 4. エラーレスポンスの返却

### 4.1 エラーコードの対応

| エラー | HTTPステータス | 理由 |
|--------|---------------|------|
| Content-Length なし | 411 Length Required | Content-Lengthヘッダーが必須 |
| Content-Length 超過 | 413 Payload Too Large | リクエストが大きすぎる |
| ファイル数超過 | 400 Bad Request | パラメータ不正 |
| ファイルサイズ超過 | 413 Payload Too Large | ファイルが大きすぎる |
| パース失敗 | 400 Bad Request | フォーマット不正 |

### 4.2 エラーハンドラーの追加

[error.py](../error.py) に追加：

```python
def handle_411() -> Response:
    """411 Length Required"""
    title = '411 Length Required'
    h1 = '411 Length Required'
    content = '\t<p>Content-Length header is required</p>\n'

    body = create_html(title, h1, content)
    length = len(body.encode('utf-8', errors='replace'))

    return Response(
        status=411,
        reason='Length Required',
        headers={
            'Content-Type': 'text/html; charset=utf-8',
            'Content-Length': length
        },
        body=body
    )


def handle_413() -> Response:
    """413 Payload Too Large"""
    title = '413 Payload Too Large'
    h1 = '413 Payload Too Large'
    content = '\t<p>Request payload is too large</p>\n'

    body = create_html(title, h1, content)
    length = len(body.encode('utf-8', errors='replace'))

    return Response(
        status=413,
        reason='Payload Too Large',
        headers={
            'Content-Type': 'text/html; charset=utf-8',
            'Content-Length': length
        },
        body=body
    )
```

### 4.3 メイン処理での使用

[09_ex29.py](../09_ex29.py) のhandle_client関数：

```python
from error import handle_400, handle_404, handle_408, handle_411, handle_413, handle_500

def handle_client(client_socket, client_address):
    try:
        # ...

        # get_request関数でリクエスト情報を保存
        request_obj = Request()
        result = get_request(client_socket, request_obj)

        if result == -1:
            # エラー理由を判定
            if request_obj.length is None:
                # Content-Lengthなし
                response_obj = handle_411()
            elif request_obj.length > config.MAX_CONTENT_LENGTH:
                # サイズ超過
                response_obj = handle_413()
            else:
                # その他のエラー
                response_obj = handle_400()

            response_bytes = response_obj.to_bytes()
            client_socket.sendall(response_bytes)
            return

        # ...
```

---

## 5. メモリ効率的な実装（発展）

### 5.1 問題：すべてメモリに保持すると危険

現在の実装:
```python
# body_part全体をメモリに保持
body_part = buffer[header_end + 4:]
while total_read < content_length:
    chunk = client_socket.recv(chunk_size)
    body_part += chunk  # ← メモリ使用量が増え続ける
```

100MBのファイルがアップロードされると、100MBのメモリを使用します。

### 5.2 解決策：ストリーミング処理

```python
def parse_multipart_streaming(client_socket, boundary: str, content_length: int, already_read: bytes):
    """
    ストリーミング方式でmultipart/form-dataをパース
    大きなファイルを直接ディスクに書き込む
    """
    import tempfile

    result_fields = {}
    result_files = {}

    file_count = 0
    boundary_bytes = f'--{boundary}'.encode('utf-8')

    # 一時ディレクトリ
    temp_dir = Path('./temp_uploads')
    temp_dir.mkdir(exist_ok=True)

    # 現在のバッファ
    buffer = already_read
    remaining = content_length - len(already_read)

    while remaining > 0:
        # バッファが小さければ追加読み込み
        if len(buffer) < 8192:
            chunk_size = min(8192, remaining)
            chunk = client_socket.recv(chunk_size)
            buffer += chunk
            remaining -= len(chunk)

        # boundaryを探す
        boundary_pos = buffer.find(boundary_bytes)

        if boundary_pos == -1:
            # boundaryが見つからない場合は待つ
            continue

        # パート部分を取り出す
        part = buffer[:boundary_pos]
        buffer = buffer[boundary_pos + len(boundary_bytes):]

        # ヘッダーとデータを分離
        header_end = part.find(b'\r\n\r\n')
        if header_end == -1:
            continue

        headers = part[:header_end].decode('utf-8', errors='replace')
        data = part[header_end + 4:]

        # Content-Dispositionをパース
        name, filename, content_type = parse_content_disposition(headers)

        if filename:
            # ファイルの場合は一時ファイルに保存
            file_count += 1
            if file_count > config.MAX_FILES:
                logging.error('Too many files')
                return None

            temp_file = temp_dir / f'{file_count}_{filename}'
            temp_file.write_bytes(data)

            result_files[name] = {
                'filename': filename,
                'content_type': content_type,
                'temp_path': str(temp_file),
                'size': len(data)
            }
        else:
            # 通常フィールド
            result_fields[name] = data.decode('utf-8', errors='replace')

    return {
        'fields': result_fields,
        'files': result_files
    }
```

**注意**: ストリーミング実装は複雑なので、最初はシンプルな実装から始めることを推奨します。

---

## 6. 実装チェックリスト

### 必須実装

- [ ] Content-Lengthの検証
- [ ] 最大Content-Lengthの制限（例: 100MB）
- [ ] ファイル数の制限（例: 10個）
- [ ] 個別ファイルサイズの制限（例: 10MB）
- [ ] 通常フィールドサイズの制限（例: 1MB）
- [ ] エラー時の適切なHTTPステータス返却（411, 413, 400）
- [ ] ログ出力（ファイル数、サイズ、エラー原因）

### 推奨実装

- [ ] 全体サイズの制限
- [ ] ファイル名のサニタイズ
- [ ] ファイルタイプの検証
- [ ] タイムアウト設定（config.TIMEOUT_INT）
- [ ] 一時ファイルのクリーンアップ

### 将来的な改善

- [ ] ストリーミング処理（大容量ファイル対応）
- [ ] ディスク容量チェック
- [ ] レート制限（同一IPからの連続アップロード制限）
- [ ] ウイルススキャン

---

## 7. テスト方法

### 7.1 正常系テスト

```bash
# 1ファイル
curl -X POST http://localhost:8080/upload \
  -F "username=Alice" \
  -F "file=@test.jpg"

# 複数ファイル
curl -X POST http://localhost:8080/upload \
  -F "file1=@test1.jpg" \
  -F "file2=@test2.jpg" \
  -F "file3=@test3.jpg"
```

### 7.2 異常系テスト

```bash
# ファイル数超過（11個送信）
curl -X POST http://localhost:8080/upload \
  -F "file1=@1.jpg" \
  -F "file2=@2.jpg" \
  ... \
  -F "file11=@11.jpg"

# 巨大ファイル（100MB以上）
dd if=/dev/zero of=large.bin bs=1M count=101
curl -X POST http://localhost:8080/upload \
  -F "file=@large.bin"

# Content-Lengthなし（エラーになるはず）
curl -X POST http://localhost:8080/upload \
  -H "Transfer-Encoding: chunked" \
  --data-binary @test.jpg
```

### 7.3 メモリ使用量の監視

```bash
# サーバー起動
python3 09_ex29.py &
PID=$!

# メモリ監視
watch -n 1 "ps aux | grep $PID | grep -v grep"

# アップロードテスト
curl -X POST http://localhost:8080/upload \
  -F "file=@large_file.bin"
```

---

## まとめ

### 重要なポイント

1. **Content-Lengthは信頼できる情報ではない**
   - クライアントが偽装可能
   - 実際の読み込みサイズを監視する

2. **複数の制限を組み合わせる**
   - ファイル数制限
   - 個別ファイルサイズ制限
   - 全体サイズ制限

3. **エラー時は適切なHTTPステータスを返す**
   - 411 Length Required
   - 413 Payload Too Large
   - 400 Bad Request

4. **ログを残す**
   - デバッグに必須
   - セキュリティ監視に使える

### 実装の優先順位

1. **必須**: Content-Length検証、ファイル数制限、サイズ制限
2. **推奨**: ファイル名サニタイズ、ファイルタイプ検証
3. **将来**: ストリーミング処理、レート制限

この戦略に従えば、安全で堅牢なファイルアップロード機能を実装できます。
