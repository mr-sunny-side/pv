# boundaryは増えないことの検証

## 実際のHTTPリクエスト例

### 例1: 3つのフィールドを送信

```http
POST /upload HTTP/1.1
Host: localhost:8080
Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryABC123
Content-Length: 456

------WebKitFormBoundaryABC123
Content-Disposition: form-data; name="username"

Alice
------WebKitFormBoundaryABC123
Content-Disposition: form-data; name="email"

alice@example.com
------WebKitFormBoundaryABC123
Content-Disposition: form-data; name="age"

25
------WebKitFormBoundaryABC123--
```

**boundary値**: `----WebKitFormBoundaryABC123` （最初から最後まで同じ）

---

### 例2: 10個のファイルを送信

```http
POST /upload HTTP/1.1
Host: localhost:8080
Content-Type: multipart/form-data; boundary=XYZ789
Content-Length: 123456

------XYZ789
Content-Disposition: form-data; name="file1"; filename="image1.jpg"
Content-Type: image/jpeg

<バイナリデータ1>
------XYZ789
Content-Disposition: form-data; name="file2"; filename="image2.jpg"
Content-Type: image/jpeg

<バイナリデータ2>
------XYZ789
Content-Disposition: form-data; name="file3"; filename="image3.jpg"
Content-Type: image/jpeg

<バイナリデータ3>
... （file4～file9も同じboundary）
------XYZ789
Content-Disposition: form-data; name="file10"; filename="image10.jpg"
Content-Type: image/jpeg

<バイナリデータ10>
------XYZ789--
```

**boundary値**: `XYZ789` （10個のファイルでも同じboundaryを使用）

---

## boundaryの決まり方

### 1. クライアント側（ブラウザ）が決定

```javascript
// JavaScriptの例
const formData = new FormData();
formData.append('username', 'Alice');
formData.append('file', fileInput.files[0]);

fetch('/upload', {
    method: 'POST',
    body: formData  // ← ブラウザが自動的にboundaryを生成
});
```

ブラウザが生成するContent-Typeヘッダー:
```
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW
```

### 2. boundaryの生成ルール

- **リクエストごとに1回だけ生成される**
- データ内容と重複しないようにランダムな文字列を使う
- 通常は長いランダム文字列（例: `----WebKitFormBoundary7MA4YWxkTrZu0gW`）

### 3. boundaryは変わらない

```python
# Python requestsライブラリの例
import requests

files = {
    'file1': open('image1.jpg', 'rb'),
    'file2': open('image2.jpg', 'rb'),
    'file3': open('image3.jpg', 'rb'),
}

# ↓ 内部で1つのboundaryが生成され、すべてのファイルに使われる
response = requests.post('http://localhost:8080/upload', files=files)
```

---

## チャンク転送との違い

### multipart/form-data（boundary固定）

```http
POST /upload HTTP/1.1
Content-Type: multipart/form-data; boundary=ABC123
Content-Length: 500           ← 全体のサイズが分かっている

------ABC123                  ← boundary（固定）
Content-Disposition: form-data; name="field1"

data1
------ABC123                  ← 同じboundary
Content-Disposition: form-data; name="field2"

data2
------ABC123--                ← 同じboundary
```

### Transfer-Encoding: chunked（サイズが都度変わる）

```http
POST /upload HTTP/1.1
Transfer-Encoding: chunked    ← チャンク転送を宣言
Content-Length なし           ← サイズは不明

1A                            ← チャンク1のサイズ（16進数で26バイト）
This is the first chunk.
                              ← 改行
10                            ← チャンク2のサイズ（16進数で16バイト）
Second chunk.
                              ← 改行
0                             ← 終了を示す0サイズチャンク
                              ← 改行
```

**違い**:
- multipart: boundaryは固定、Content-Lengthが必須
- chunked: サイズが動的、Content-Lengthは不要

---

## 実装上の注意点

### ✅ boundary検出（1回だけ）

```python
def extract_boundary(content_type: str) -> str | None:
    """
    Content-Typeヘッダーからboundaryを抽出
    この関数は1回だけ呼ばれ、結果は固定値として使われる
    """
    if 'boundary=' not in content_type:
        return None

    parts = content_type.split('boundary=')
    if len(parts) < 2:
        return None

    boundary = parts[1].strip()
    if boundary.startswith('"') and boundary.endswith('"'):
        boundary = boundary[1:-1]

    return boundary

# 使用例
content_type = "multipart/form-data; boundary=----WebKitFormBoundary7MA"
boundary = extract_boundary(content_type)  # ← 1回だけ呼ぶ
print(boundary)  # "----WebKitFormBoundary7MA"

# この後、boundaryは変わらない
```

### ✅ パース処理（境界文字列で分割）

```python
def parse_multipart(body_bytes: bytes, boundary: str) -> dict:
    """
    boundaryは引数として1つだけ受け取る
    この値は最初から最後まで変わらない
    """
    # 境界文字列の準備（--を前に付ける）
    boundary_bytes = f'--{boundary}'.encode('utf-8')
    end_boundary_bytes = f'--{boundary}--'.encode('utf-8')

    # ボディ全体を境界文字列で分割
    parts = body_bytes.split(boundary_bytes)
    # ↑ 同じboundary_bytesで全体を分割するだけ

    result = {}
    for part in parts[1:]:  # 最初の要素は空
        if end_boundary_bytes in part:
            break  # 終了マーカーが見つかったら終了

        # 各パートを処理...

    return result
```

### ❌ 間違った実装例（boundaryを探し続ける）

```python
# 間違い: boundaryが増えると誤解している例
def wrong_parse(body_bytes: bytes):
    boundaries = []  # ← boundaryは1つだけなのでリストは不要

    # 間違い: ループしてboundaryを探し続ける必要はない
    while True:
        boundary = find_next_boundary(body_bytes)  # ← 不要
        if not boundary:
            break
        boundaries.append(boundary)

    # 正しくは、最初に1つboundaryを取得して、
    # それで全体を分割するだけ
```

---

## まとめ

### boundaryについての真実

| 項目 | 説明 |
|------|------|
| 数 | **1リクエストにつき1つだけ** |
| 決定タイミング | リクエスト送信前にクライアントが決定 |
| 変更 | **途中で変わることは絶対にない** |
| 用途 | 複数のパートを区切るための固定文字列 |
| 長さ | 通常30〜70文字程度 |

### 実装のポイント

1. ✅ Content-Typeヘッダーから**1回だけ**boundaryを抽出
2. ✅ そのboundaryで**全体を分割**
3. ✅ boundaryは**変数に保存して使い回す**
4. ❌ boundaryを探し続ける必要は**ない**
5. ❌ boundaryが増えることは**ない**

### 安心してください

> **multipart/form-dataのboundaryは、リクエストごとに1つ固定です。**
> **無尽蔵に増えることは仕様上ありえません。**

HTTP/1.1のRFC 7578で厳密に規定されており、すべてのブラウザとHTTPクライアントがこの仕様に従っています。
