# multipart/form-data形式 完全ガイド

## 1. multipart/form-dataとは？

**multipart/form-data**は、HTTPでファイルやバイナリデータを送信するためのエンコーディング形式です。

### なぜ「multipart（複数部分）」なのか？

「ファイルを分割して送信する」という意味ではなく、**1つのHTTPリクエストの中に複数の異なるデータ（テキストフィールド、ファイルなど）を含めることができる**という意味です。各データは「パート（part）」として区切られます。

### 既存のapplication/x-www-form-urlencodedとの違い

| 項目 | application/x-www-form-urlencoded | multipart/form-data |
|------|-----------------------------------|---------------------|
| データ形式 | `key1=value1&key2=value2` | 境界文字列で区切られた複数のパート |
| バイナリデータ | 不可（Base64などでエンコードが必要） | 可能（そのまま送信） |
| ファイルアップロード | 非効率 | 効率的 |
| データサイズ | 小さいテキストデータ向け | 大きなファイル向け |

---

## 2. multipart/form-dataの構造

### 実際のリクエスト例

```http
POST /upload HTTP/1.1
Host: localhost:8080
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Length: 12345

------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="username"

Alice
------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="profile_pic"; filename="photo.jpg"
Content-Type: image/jpeg

<バイナリデータがここに入る>
------WebKitFormBoundary7MA4YWxkTrZu0gW--
```

### 構造の詳細解説

#### (1) Content-Typeヘッダー
```
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW
```
- `boundary`パラメータ：各パートを区切るための**境界文字列**を指定
- 境界文字列はリクエストごとにランダムに生成される（データ内容と重複しないように）

#### (2) 各パートの構造
```
------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="username"

Alice
```

- **境界文字列の前に`--`が2つ付く**（重要！）
- `Content-Disposition`：パートのメタデータ
  - `name="username"`：フォームフィールドの名前
  - `filename="photo.jpg"`：ファイル名（ファイルの場合のみ）
- **空行（`\r\n\r\n`）の後にデータ本体**

#### (3) ファイルパートの構造
```
------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="profile_pic"; filename="photo.jpg"
Content-Type: image/jpeg

<バイナリデータ>
```

- ファイルの場合は`Content-Type`ヘッダーも含まれる
- データはバイナリのまま送信される（エンコード不要）

#### (4) 終了マーカー
```
------WebKitFormBoundary7MA4YWxkTrZu0gW--
```
- **最後の境界文字列の後ろにも`--`が2つ付く**
- これでmultipartデータの終了を示す

---

## 3. 実装のポイント

### 3.1 パース処理の流れ

```
1. Content-Typeヘッダーからboundary文字列を抽出
   ↓
2. ボディ全体を読み込む
   ↓
3. boundary文字列でボディを分割
   ↓
4. 各パートのヘッダーとデータを分離
   ↓
5. Content-Dispositionからname、filenameを抽出
   ↓
6. データを保存（テキストまたはバイナリ）
```

### 3.2 現在のコードの修正ポイント

#### [http.py:86-87](http.py#L86-L87) の問題点
```python
# 現在の実装
body_part = body_part.decode('utf-8', errors='replace')
request_obj.body = parse_qs(body_part)
```

**問題**：
- `decode('utf-8')`はバイナリデータ（画像など）を壊す
- `parse_qs()`は`application/x-www-form-urlencoded`専用

**解決策**：
- Content-Typeヘッダーを確認
- `multipart/form-data`の場合は専用のパース処理を実行
- バイナリデータはそのまま保持

### 3.3 実装アルゴリズム

```python
def parse_multipart(body_bytes: bytes, boundary: str) -> dict:
    """
    multipart/form-dataをパースする

    Args:
        body_bytes: リクエストボディ全体（バイナリ）
        boundary: 境界文字列

    Returns:
        {field_name: (filename, content_type, data)}
    """
    result = {}

    # 1. 境界文字列の準備（--を前に付ける）
    boundary_bytes = f'--{boundary}'.encode('utf-8')
    end_boundary_bytes = f'--{boundary}--'.encode('utf-8')

    # 2. ボディを境界文字列で分割
    parts = body_bytes.split(boundary_bytes)

    # 3. 各パートを処理
    for part in parts[1:]:  # 最初の要素は空なのでスキップ
        if end_boundary_bytes in part:
            break

        # 4. ヘッダーとデータを分離
        header_end = part.find(b'\r\n\r\n')
        if header_end == -1:
            continue

        headers = part[:header_end].decode('utf-8', errors='replace')
        data = part[header_end + 4:]  # \r\n\r\nの後

        # 末尾の\r\nを削除
        if data.endswith(b'\r\n'):
            data = data[:-2]

        # 5. Content-Dispositionをパース
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

        # 6. 結果を保存
        if name:
            if filename:
                # ファイルの場合はバイナリのまま保存
                result[name] = (filename, content_type, data)
            else:
                # 通常のフィールドはテキストとして保存
                try:
                    text_data = data.decode('utf-8')
                    result[name] = (None, content_type, text_data)
                except:
                    result[name] = (None, content_type, data)

    return result
```

### 3.4 境界文字列の抽出

```python
def extract_boundary(content_type_header: str) -> str | None:
    """
    Content-Typeヘッダーからboundary文字列を抽出

    例: "multipart/form-data; boundary=----WebKitForm..."
        → "----WebKitForm..."
    """
    if 'boundary=' not in content_type_header:
        return None

    parts = content_type_header.split('boundary=')
    if len(parts) < 2:
        return None

    boundary = parts[1].strip()

    # boundaryがクォートで囲まれている場合は除去
    if boundary.startswith('"') and boundary.endswith('"'):
        boundary = boundary[1:-1]

    return boundary
```

---

## 4. 実装手順

### Step 1: http.pyの修正

[http.py:9-16](http.py#L9-L16) のRequestクラスに新しいフィールドを追加：

```python
class Request:
    def __init__(self):
        self.method = None
        self.path = None
        self.version = None
        self.length = None
        self.query = {}
        self.body = {}
        self.content_type = None  # 追加
        self.files = {}           # 追加（ファイル専用）
```

### Step 2: Content-Typeヘッダーの保存

[http.py:66-78](http.py#L66-L78) のヘッダーパース処理を修正：

```python
## POSTメソッドの読み込み・保存
# Content-TypeとContent-Lengthを取得
for header in header_line[1:]:
    parts = header.split(':', 1)
    if len(parts) < 2:
        continue

    key = parts[0].strip()
    value = parts[1].strip()

    if key == 'Content-Length':
        request_obj.length = int(value)
    elif key == 'Content-Type':
        request_obj.content_type = value
```

### Step 3: ボディのパース処理を条件分岐

[http.py:85-88](http.py#L85-L88) を修正：

```python
# Content-Typeに応じてパース処理を分岐
if request_obj.content_type and 'multipart/form-data' in request_obj.content_type:
    # multipart/form-dataのパース
    boundary = extract_boundary(request_obj.content_type)
    if boundary:
        parsed_data = parse_multipart(body_part, boundary)

        # filesとbodyに分類
        for name, (filename, content_type, data) in parsed_data.items():
            if filename:
                request_obj.files[name] = {
                    'filename': filename,
                    'content_type': content_type,
                    'data': data
                }
            else:
                request_obj.body[name] = [data]  # parse_qsと同じ形式
    else:
        logging.error('get_request: Cannot extract boundary')
        return -1
else:
    # 従来のapplication/x-www-form-urlencodedのパース
    body_part = body_part.decode('utf-8', errors='replace')
    request_obj.body = parse_qs(body_part)
```

### Step 4: ファイル保存の実装（route.pyなど）

```python
@route('/upload')
def handle_upload(request_obj: Request, **kwargs) -> Response:
    """ファイルアップロードハンドラー"""

    # ファイルが送信されたか確認
    if 'file' not in request_obj.files:
        return Response(status=400, reason='Bad Request',
                       body='<h1>No file uploaded</h1>')

    file_info = request_obj.files['file']
    filename = file_info['filename']
    file_data = file_info['data']

    # ファイルを保存
    upload_dir = Path('./uploads')
    upload_dir.mkdir(exist_ok=True)

    save_path = upload_dir / filename
    save_path.write_bytes(file_data)

    # レスポンス
    html = f'''
    <!DOCTYPE html>
    <html>
    <body>
        <h1>Upload Success!</h1>
        <p>Filename: {html.escape(filename)}</p>
        <p>Size: {len(file_data)} bytes</p>
    </body>
    </html>
    '''

    return Response(status=200, reason='OK', body=html)
```

---

## 5. テスト方法

### HTMLフォームの作成

[static/upload.html](static/upload.html) を作成：

```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="utf-8">
    <title>File Upload Test</title>
</head>
<body>
    <h1>ファイルアップロードテスト</h1>
    <form action="/upload" method="POST" enctype="multipart/form-data">
        <label>名前: <input type="text" name="username" required></label><br>
        <label>ファイル: <input type="file" name="file" required></label><br>
        <button type="submit">アップロード</button>
    </form>
</body>
</html>
```

**重要**: `<form>`タグに`enctype="multipart/form-data"`が必須！

### curlでのテスト

```bash
# テキストファイルをアップロード
curl -X POST http://localhost:8080/upload \
  -F "username=Alice" \
  -F "file=@test.txt"

# 画像ファイルをアップロード
curl -X POST http://localhost:8080/upload \
  -F "username=Bob" \
  -F "file=@photo.jpg"
```

---

## 6. セキュリティ上の注意点

### 6.1 ファイル名のサニタイズ

```python
import re
from pathlib import Path

def sanitize_filename(filename: str) -> str:
    """
    危険なファイル名を安全にする
    """
    # パストラバーサル攻撃を防ぐ
    filename = Path(filename).name

    # 危険な文字を削除
    filename = re.sub(r'[^\w\.\-]', '_', filename)

    # 隠しファイルを防ぐ
    if filename.startswith('.'):
        filename = '_' + filename

    return filename

# 使用例
safe_filename = sanitize_filename(file_info['filename'])
save_path = upload_dir / safe_filename
```

### 6.2 ファイルサイズの制限

```python
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

if len(file_data) > MAX_FILE_SIZE:
    return Response(status=413, reason='Payload Too Large',
                   body='<h1>File too large</h1>')
```

### 6.3 ファイルタイプの検証

```python
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.pdf'}

file_ext = Path(filename).suffix.lower()
if file_ext not in ALLOWED_EXTENSIONS:
    return Response(status=400, reason='Bad Request',
                   body='<h1>File type not allowed</h1>')
```

### 6.4 ディレクトリトラバーサル対策

```python
# 保存先が意図したディレクトリ内か確認
upload_dir = Path('./uploads').resolve()
save_path = (upload_dir / safe_filename).resolve()

if not str(save_path).startswith(str(upload_dir)):
    logging.error('Directory traversal attempt detected')
    return Response(status=400, reason='Bad Request',
                   body='<h1>Invalid filename</h1>')
```

---

## 7. よくあるエラーと対処法

| エラー | 原因 | 解決策 |
|--------|------|--------|
| `UnicodeDecodeError` | バイナリデータをdecode()した | バイナリはそのまま保持する |
| boundary not found | Content-Typeヘッダーが間違っている | ヘッダーを正しくパースする |
| データが壊れる | 境界文字列の`--`を忘れた | `--boundary`の形式を確認 |
| 最後のパートが読めない | 終了マーカー`--boundary--`を見逃した | 終了判定を正しく実装 |
| ファイルサイズが0 | `\r\n\r\n`の後の4バイトを計算ミス | `header_end + 4`を確認 |

---

## 8. まとめ

### multipart/form-dataの特徴
- ✅ バイナリファイルを効率的に送信できる
- ✅ 1つのリクエストで複数のファイル＋テキストフィールドを送信できる
- ✅ 境界文字列で各パートを区切る
- ⚠️ パース処理が複雑になる
- ⚠️ セキュリティ対策が必須

### 実装のキーポイント
1. **Content-Typeヘッダーからboundaryを抽出**
2. **バイナリデータはdecode()しない**
3. **境界文字列の前後の`--`に注意**
4. **ファイル名のサニタイズは必須**
5. **ファイルサイズの制限を設ける**

---

## 参考資料

- [RFC 7578 - Returning Values from Forms: multipart/form-data](https://datatracker.ietf.org/doc/html/rfc7578)
- [MDN - FormData](https://developer.mozilla.org/ja/docs/Web/API/FormData)
- [OWASP - File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
