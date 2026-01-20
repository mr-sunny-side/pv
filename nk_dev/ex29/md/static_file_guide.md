# 静的ファイル配信の実装ガイド

## 概要

静的ファイル配信とは、HTML、CSS、JavaScript、画像などのファイルをそのままクライアントに送信する機能です。
現在のサーバーは「動的に生成したHTML」を返していますが、これに加えて「ファイルシステム上の実際のファイル」を返せるようにします。

---

## 必要なモジュールの解説

### 1. `os` モジュール

**存在意義**: オペレーティングシステムとやり取りするためのモジュール

**静的ファイル配信で使う機能**:

```python
import os

# ファイルが存在するか確認
os.path.exists('/path/to/file.html')  # True or False

# ファイルかどうか確認（ディレクトリではない）
os.path.isfile('/path/to/file.html')  # True or False

# パスを結合（OSに応じて適切な区切り文字を使う）
os.path.join('static', 'css', 'style.css')  # 'static/css/style.css'

# 絶対パスに変換
os.path.abspath('static/file.html')  # '/home/user/project/static/file.html'

# パスを正規化（../ などを解決）
os.path.normpath('/static/../static/file.html')  # '/static/file.html'
```

### 2. `pathlib.Path` モジュール

**存在意義**: `os.path` のオブジェクト指向版。より直感的にパス操作ができる

**静的ファイル配信で使う機能**:

```python
from pathlib import Path

# Pathオブジェクトを作成
file_path = Path('static/css/style.css')

# ファイルが存在するか
file_path.exists()  # True or False

# ファイルかどうか
file_path.is_file()  # True or False

# ディレクトリかどうか
file_path.is_dir()  # True or False

# 絶対パスに変換
file_path.resolve()  # PosixPath('/home/user/project/static/css/style.css')

# ファイルを読み込む（テキスト）
content = file_path.read_text(encoding='utf-8')

# ファイルを読み込む（バイナリ）← 画像などに使う
content = file_path.read_bytes()

# 拡張子を取得
file_path.suffix  # '.css'

# ファイル名を取得
file_path.name  # 'style.css'

# 親ディレクトリを取得
file_path.parent  # PosixPath('static/css')

# パスを結合（/ 演算子が使える）
base = Path('static')
full_path = base / 'css' / 'style.css'  # PosixPath('static/css/style.css')
```

### 3. `mimetypes` モジュール

**存在意義**: ファイルの拡張子から適切なContent-Typeを判定する

HTTPレスポンスでは `Content-Type` ヘッダーでファイルの種類を伝える必要があります。
ブラウザはこのヘッダーを見て、ファイルをどう処理するか決めます。

```python
import mimetypes

# 拡張子からMIMEタイプを取得
mimetypes.guess_type('style.css')      # ('text/css', None)
mimetypes.guess_type('script.js')      # ('application/javascript', None)
mimetypes.guess_type('image.png')      # ('image/png', None)
mimetypes.guess_type('photo.jpg')      # ('image/jpeg', None)
mimetypes.guess_type('index.html')     # ('text/html', None)
mimetypes.guess_type('data.json')      # ('application/json', None)
mimetypes.guess_type('unknown.xyz')    # (None, None)  ← 不明な場合

# 戻り値は (MIMEタイプ, エンコーディング) のタプル
# エンコーディングは通常 None（gzipなどの場合に値が入る）
```

**主なMIMEタイプ一覧**:

| 拡張子 | MIMEタイプ | 説明 |
|--------|-----------|------|
| .html | text/html | HTMLファイル |
| .css | text/css | スタイルシート |
| .js | application/javascript | JavaScript |
| .json | application/json | JSONデータ |
| .png | image/png | PNG画像 |
| .jpg, .jpeg | image/jpeg | JPEG画像 |
| .gif | image/gif | GIF画像 |
| .svg | image/svg+xml | SVG画像 |
| .ico | image/x-icon | アイコン |
| .txt | text/plain | プレーンテキスト |

---

## 実装の流れ

### Step 1: 静的ファイル用のディレクトリを決める

```
ex29/
├── 06_ex29.py      ← サーバースクリプト
└── static/         ← 静的ファイル置き場
    ├── index.html
    ├── css/
    │   └── style.css
    ├── js/
    │   └── script.js
    └── images/
        └── logo.png
```

### Step 2: 静的ファイルを配信する関数を作成

```python
from pathlib import Path
import mimetypes

# 静的ファイルのルートディレクトリ
STATIC_DIR = Path(__file__).parent / 'static'

def serve_static_file(request_path):
    """
    リクエストパスに対応する静的ファイルを返す

    Args:
        request_path: リクエストされたパス（例: '/css/style.css'）

    Returns:
        Response オブジェクト、またはファイルが見つからない場合は None
    """

    # 先頭の / を除去してパスを作成
    # '/css/style.css' → 'css/style.css'
    relative_path = request_path.lstrip('/')

    # 静的ディレクトリと結合
    file_path = STATIC_DIR / relative_path

    # セキュリティチェック: ディレクトリトラバーサル攻撃を防ぐ
    # （../../../etc/passwd のようなパスを防ぐ）
    try:
        file_path = file_path.resolve()
        if not str(file_path).startswith(str(STATIC_DIR.resolve())):
            return None  # 静的ディレクトリ外へのアクセスは拒否
    except Exception:
        return None

    # ファイルが存在しない、またはディレクトリの場合
    if not file_path.exists() or not file_path.is_file():
        return None

    # MIMEタイプを取得
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if mime_type is None:
        mime_type = 'application/octet-stream'  # 不明な場合のデフォルト

    # ファイルを読み込む
    # テキスト系かバイナリ系かで読み方を変える
    if mime_type.startswith('text/') or mime_type in ['application/javascript', 'application/json']:
        # テキストファイル
        content = file_path.read_text(encoding='utf-8')
    else:
        # バイナリファイル（画像など）
        content = file_path.read_bytes()

    # Responseオブジェクトを返す
    return Response(
        status=200,
        reason='OK',
        headers={'Content-Type': mime_type},
        body=content
    )
```

### Step 3: handle_client で静的ファイルを優先的にチェック

```python
def handle_client(client_socket):
    # ... 既存のパース処理 ...

    # まず静的ファイルをチェック
    static_response = serve_static_file(request_obj.path)
    if static_response:
        # 静的ファイルが見つかった
        response_obj = static_response
    else:
        # 既存のルーティング処理
        response_obj = Response()
        matched = None
        for pattern, handler in routes:
            # ... 既存のコード ...
```

---

## 注意点

### 1. バイナリファイルの扱い

現在の `Response.to_bytes()` は文字列を前提としています。
画像などのバイナリファイルを扱うには修正が必要です：

```python
def to_bytes(self):
    response = f'HTTP/1.1 {self.status} {self.reason}\r\n'

    for label, detail in self.headers.items():
        response += f'{label}: {detail}\r\n'

    response += '\r\n'

    # ヘッダー部分をバイト列に変換
    header_bytes = response.encode('utf-8')

    # ボディがすでにバイト列ならそのまま、文字列なら変換
    if isinstance(self.body, bytes):
        body_bytes = self.body
    else:
        body_bytes = self.body.encode('utf-8', errors='replace')

    return header_bytes + body_bytes
```

### 2. Content-Length の計算

バイナリファイルの場合、`len()` で直接バイト数を取得できます：

```python
if isinstance(response_obj.body, bytes):
    content_length = len(response_obj.body)
else:
    content_length = len(response_obj.body.encode('utf-8', errors='replace'))
```

### 3. セキュリティ（ディレクトリトラバーサル）

`/../` を使って静的ディレクトリ外のファイルにアクセスされないよう注意が必要です：

```
悪意のあるリクエスト: GET /../../../etc/passwd HTTP/1.1
```

`Path.resolve()` で絶対パスに変換し、静的ディレクトリ内かどうかを確認します。

---

## 実装の優先順位

1. **モジュールのインポート追加** (`pathlib`, `mimetypes`)
2. **STATIC_DIR 定数の定義**
3. **serve_static_file 関数の作成**
4. **Response.to_bytes() のバイナリ対応**
5. **handle_client での静的ファイルチェック追加**
6. **テスト用の静的ファイル作成**（`static/` ディレクトリ）

---

## 簡単なテスト方法

1. `static/test.html` を作成:
```html
<!DOCTYPE html>
<html>
<head><title>Static Test</title></head>
<body><h1>This is a static file!</h1></body>
</html>
```

2. サーバーを起動して `http://127.0.0.1:8080/test.html` にアクセス

3. 正しく表示されれば成功
