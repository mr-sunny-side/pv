# Pythonのbytes型とstr型の違い

## 問題の状況

BMPファイルヘッダを読み込んで表示する際、`signature` だけが `b'BM'` と表示されてしまう。

```python
signature, file_size, img_offset = struct.unpack('<2sIxxxxI', file_header)

print_result(title, 'File Type', str(signature))
# 出力: b'BM'  ← b がついている

print_result(None, 'File Size', str(file_size))
# 出力: 30054  ← 正常
```

## 原因

`struct.unpack()` のフォーマット指定子によって、返される型が異なる。

### フォーマット指定子と返される型

| フォーマット | 意味 | 返される型 | 例 |
|------------|------|-----------|-----|
| `2s` | 2バイトの文字列 | **bytes型** | `b'BM'` |
| `I` | 符号なし4バイト整数 | **int型** | `30054` |
| `H` | 符号なし2バイト整数 | **int型** | `24` |

## bytes型とstr型の違い

Pythonでは、バイナリデータ（bytes型）とテキストデータ（str型）は明確に区別される。

```python
# bytes型
signature = b'BM'
type(signature)  # <class 'bytes'>

# str型
text = 'BM'
type(text)  # <class 'str'>
```

### str() の挙動の違い

```python
# bytes型に str() を適用
str(b'BM')
# 結果: "b'BM'"  ← bytes型オブジェクトの文字列表現

# int型に str() を適用
str(30054)
# 結果: '30054'  ← 数値が文字列に変換される
```

**重要**: `str(bytes_object)` は「このオブジェクトを説明する文字列」を返すだけで、デコードはしない。

## 解決方法

### 方法1: decode() メソッドを使う（推奨）

```python
# 修正前
print_result(title, 'File Type', str(signature))
# 出力: b'BM'

# 修正後
print_result(title, 'File Type', signature.decode('ascii'))
# 出力: BM
```

または

```python
print_result(title, 'File Type', signature.decode())
# デフォルトエンコーディング（UTF-8）でデコード
# 出力: BM
```

### 方法2: unpack時に処理を分ける

```python
# 現在
signature, file_size, img_offset = struct.unpack('<2sIxxxxI', file_header)
# signature は bytes型

# 改善版
signature_bytes, file_size, img_offset = struct.unpack('<2sIxxxxI', file_header)
signature = signature_bytes.decode('ascii')
# signature は str型
```

## bytes型とstr型の相互変換

### bytes → str (デコード)

```python
b'BM'.decode('ascii')   # 'BM'
b'BM'.decode('utf-8')   # 'BM'
b'BM'.decode()          # 'BM' (デフォルトはUTF-8)
```

### str → bytes (エンコード)

```python
'BM'.encode('ascii')    # b'BM'
'BM'.encode('utf-8')    # b'BM'
'BM'.encode()           # b'BM' (デフォルトはUTF-8)
```

## まとめ

1. **bytes型**: バイナリデータ（`b'BM'`）
2. **str型**: テキストデータ（`'BM'`）
3. `str(bytes_object)` はデコードしない → `"b'BM'"` という文字列になる
4. **bytes → str**: `.decode()` メソッドを使う
5. **struct.unpack()** のフォーマット指定子 `s` は bytes型を返す
6. **struct.unpack()** のフォーマット指定子 `I`, `H` などは int型を返す

## 実践例

```python
import struct

# ファイルヘッダ読み込み
with open('sample.bmp', 'rb') as f:
    file_header = f.read(14)
    signature, file_size, img_offset = struct.unpack('<2sIxxxxI', file_header)

# 誤った方法
print(f"File Type: {str(signature)}")
# 出力: File Type: b'BM'

# 正しい方法
print(f"File Type: {signature.decode('ascii')}")
# 出力: File Type: BM

# int型は str() で問題ない
print(f"File Size: {str(file_size)} bytes")
# 出力: File Size: 30054 bytes
```
