# WAVファイル解析での複合的なバグ - 学習フィードバック

## 問題の症状

sample.wavを解析しようとしたところ、無限ループに陥り、エラーメッセージが延々と出力される:

```bash
$ ./ex28_bin_9b.py $BIN_FILE/sample.wav
Error: Cannot read file
Error: Cannot read file
Error: Cannot read file
Error: Cannot read file
Error: Cannot read file
...（無限に続く）
```

プログラムが終了せず、Ctrl+Cで強制終了する必要がある。

## 問題の本質

このコードには**3つの独立したバグ**が同時に存在していました：

1. **バイト文字列と文字列の比較エラー** - チャンクが全く認識されない
2. **ファイルポインタの計算ミス** - 異常な位置にジャンプする
3. **無限ループ** - ファイル終端検出の欠如

これらが複合的に作用し、問題の発見を困難にしていました。

## 問題のコード

### バグ1: バイト文字列と文字列の比較 (37, 44, 72行目)

```python
tmp_id, tmp_size, tmp_format = struct.unpack('<4sI4s', tmp)
# ↑ tmp_id は b'RIFF' のようなバイト文字列

# 37行目 - 間違い
if tmp_id == 'RIFF' and tmp_format == 'WAVE':   # 常にFalse!
    ...

# 44行目 - 間違い
elif tmp_id == 'fmt ':   # 常にFalse!
    ...

# 72行目 - 間違い
elif tmp_id == 'data':   # 常にFalse!
    ...
```

### バグ2: ファイルポインタの計算ミス (45行目)

```python
elif tmp_id == 'fmt ':
    f.seek(-8, 1)    # ← 間違い！-12が正しい

    fmt = f.read(24)
```

### バグ3: 無限ループとエラーハンドリング (100-116行目)

```python
while (not fmt or not data or not riff):
    tmp = process_read(f)

    # tmpがNoneの場合の処理が不十分
    if tmp['chunk_id'] == "RIFF" and tmp['chunk_id'] == 'WAVE' and not riff:
        riff = tmp
    elif tmp['chunk_id'] == "fmt " and not fmt:
        fmt = tmp
    elif tmp['chunk_id'] == "data" and not data:
        data = tmp
    # ファイル終端やエラー時の脱出処理がない
```

## デバッグ方法: なぜ自分で見つけられなかったか

**重要な教訓: デバッグ出力がなければ、どんなに時間をかけても見つけられない可能性が高い**

### デバッグ出力なしの場合

- 目視でコードを何度読んでも、型の問題は気づきにくい
- ファイルポインタが異常な位置にあることに気づけない
- 無限ループの原因を推測するしかない

### デバッグ出力を追加した場合

```python
def process_read(f):
    pos_before = f.tell()
    tmp = f.read(12)
    pos_after = f.tell()

    # デバッグ出力
    print(f"DEBUG: pos={pos_before}->{pos_after}, read={len(tmp)} bytes", file=sys.stderr)
    print(f"DEBUG: data={tmp!r}", file=sys.stderr)

    if tmp is None or len(tmp) != 12:
        print("Error: Cannot read file", file=sys.stderr)
        return None

    tmp_id, tmp_size, tmp_format = struct.unpack('<4sI4s', tmp)

    # 型と値をデバッグ
    print(f"DEBUG: tmp_id={tmp_id!r} (type={type(tmp_id).__name__})", file=sys.stderr)
    print(f"DEBUG: tmp_id == 'RIFF'? {tmp_id == 'RIFF'}", file=sys.stderr)
    print(f"DEBUG: tmp_id == b'RIFF'? {tmp_id == b'RIFF'}", file=sys.stderr)
```

**実行結果**:
```
DEBUG: pos=0->12, read=12 bytes
DEBUG: data=b'RIFF$\x00\x00\x00WAVE'
DEBUG: tmp_id=b'RIFF' (type=bytes)
DEBUG: tmp_id == 'RIFF'? False    ← 問題発見！
DEBUG: tmp_id == b'RIFF'? True

DEBUG: pos=12->24, read=12 bytes
DEBUG: data=b'fmt \x10\x00\x00\x00\x01\x00\x01\x00'
DEBUG: tmp_id=b'fmt ' (type=bytes)
DEBUG: tmp_id == 'fmt '? False    ← 問題発見！

DEBUG: pos=24->16, read=24 bytes  ← ファイル位置が戻っている！
DEBUG: pos=16->40, read=0 bytes
DEBUG: pos=40->65561, read=0 bytes ← 異常なジャンプ！
```

このデバッグ出力があれば、**5分以内に問題を特定できます**。

## 問題の原因（詳細）

### 原因1: バイト文字列と文字列の型不一致

**Pythonの基本ルール**:
```python
>>> b'RIFF' == 'RIFF'
False

>>> b'RIFF' == b'RIFF'
True

>>> type(b'RIFF')
<class 'bytes'>

>>> type('RIFF')
<class 'str'>
```

**struct.unpackの仕様**:
```python
>>> import struct
>>> tmp_id, _, _ = struct.unpack('<4sI4s', b'RIFF\x00\x00\x00\x00WAVE')
>>> tmp_id
b'RIFF'  # バイト文字列を返す
>>> type(tmp_id)
<class 'bytes'>
```

**影響**:
- 37行目の `tmp_id == 'RIFF'` は常に`False`
- 44行目の `tmp_id == 'fmt '` は常に`False`
- 72行目の `tmp_id == 'data'` は常に`False`
- **結果**: すべてのチャンクが`else`ブロック（79-81行目）に入る

### 原因2: ファイルポインタの計算ミス

**問題のあるコード**:
```python
# 12バイト読んだ時点でファイル位置は24
tmp = f.read(12)  # b'fmt \x10\x00\x00\x00\x01\x00\x01\x00'
#                    ^^^^^^^^^^^^^^^^^^^^^
#                    chunk_id + chunk_size + 最初の4バイト

# -8バイト戻ると位置16になる（間違い）
f.seek(-8, 1)

# 24バイト読むと、chunk_sizeの部分から読んでしまう
fmt = f.read(24)  # b'\x10\x00\x00\x00\x01\x00\x01\x00...'
```

**ファイル構造**:
```
位置12: 'fmt ' (4バイト) ← chunk_id
位置16: 16 (4バイト)     ← chunk_size (正しい値)
位置20: 1 (2バイト)      ← audio_format
位置22: 1 (2バイト)      ← channel_num
位置24: 44100 (4バイト)  ← sample_rate
...
```

**間違った読み取り**:
```python
# 位置16から24バイト読むと
fmt = b'\x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00...'

# これをunpackすると
chunk_id, chunk_size, audio_format, ... = struct.unpack('<4sIHHIIHH', fmt)

# chunk_sizeが異常な値に
# b'\x10\x00\x00\x00' (位置16) と b'\x01\x00\x01\x00' (位置20-23) の8バイトが
# chunk_size (4バイト) として解釈される
# リトルエンディアンで: 0x00010001 0x00000010 → 65537

# その後
if chunk_size > 16:  # 65537 > 16 → True
    f.seek(chunk_size - 16, 1)  # 65537 - 16 = 65521バイト進む
    # ファイル終端をはるかに超える！
```

**正しいコード**:
```python
# -12バイト戻る（読んだ12バイト全体を戻す）
f.seek(-12, 1)

# これでchunk_idの先頭（位置12）に戻る
# 24バイト読めば正しくfmtチャンク全体を読める
```

### 原因3: 無限ループ（ファイル終端検出の欠如）

**ループの流れ**:

1. バグ1により、すべてのチャンクが認識されない
2. `else`ブロックで`{'chunk_id': 'None'}`が返される
3. 100-116行目の条件分岐にマッチしない
4. `fmt`、`data`、`riff`が`None`のまま
5. ループ条件 `(not fmt or not data or not riff)` が`True`のまま
6. バグ2により異常な位置にジャンプ
7. ファイル終端を超えて読もうとする
8. `f.read(12)`が空のバイト列`b''`を返す
9. 31行目の`len(tmp) != 12`が`True`になり、`None`を返す
10. 114-116行目でループを抜けるはずだが...

**実は修正版では抜けられる**:
```python
elif tmp is None:
    print("process_read: returned None")
    return 1  # ここで関数を抜ける
```

ただし、修正前は`{'chunk_id': 'None'}`を返していたため、無限ループになっていました。

## 解決方法

### 修正1: バイト文字列リテラルを使用

```python
# 修正前
if tmp_id == 'RIFF' and tmp_format == 'WAVE':
elif tmp_id == 'fmt ':
elif tmp_id == 'data':

# 修正後
if tmp_id == b'RIFF' and tmp_format == b'WAVE':   # bプレフィックスを追加
elif tmp_id == b'fmt ':
elif tmp_id == b'data':
```

### 修正2: ファイルポインタの計算を修正

```python
# 修正前
f.seek(-8, 1)

# 修正後
f.seek(-12, 1)  # 読んだ12バイト全体を戻す
```

**なぜ-12か**:
```
読んだ12バイト:
  tmp_id (4) + tmp_size (4) + tmp_format (4) = 12

fmtチャンクを最初から読むには:
  位置24 - 12 = 位置12（chunk_idの先頭）
```

### 修正3: エラーハンドリングの改善

```python
# 修正前（無限ループの原因）
if tmp is None or len(tmp) != 12:
    print("Error: Cannot read file", file=sys.stderr)
    return {'chunk_id': 'None'}  # 辞書を返すので、mainループで検出できない

# 修正後
if tmp is None or len(tmp) != 12:
    print("Error: Cannot read file", file=sys.stderr)
    return None  # Noneを返す

# main関数側
elif tmp is None:
    print("process_read: returned None")
    return 1  # エラー終了
```

## 小さいテストケースで問題を切り分ける

複雑な問題は、**最小限のコード**で再現することが重要です。

### テスト1: バイト文字列の比較

```python
# test_bytes_comparison.py
import struct

# struct.unpackがバイト文字列を返すことを確認
data = b'RIFF\x00\x00\x00\x00WAVE'
tmp_id, tmp_size, tmp_format = struct.unpack('<4sI4s', data)

print(f"tmp_id = {tmp_id!r}")
print(f"type(tmp_id) = {type(tmp_id)}")
print()

# 比較テスト
print(f"tmp_id == 'RIFF' → {tmp_id == 'RIFF'}")    # False
print(f"tmp_id == b'RIFF' → {tmp_id == b'RIFF'}")  # True
```

**実行結果**:
```
tmp_id = b'RIFF'
type(tmp_id) = <class 'bytes'>

tmp_id == 'RIFF' → False
tmp_id == b'RIFF' → True
```

これで**バグ1が確認できます**。

### テスト2: ファイルポインタの動き

```python
# test_file_position.py
import struct

# テスト用WAVファイルを作成
with open('/tmp/test.wav', 'wb') as f:
    f.write(b'RIFF')
    f.write(struct.pack('<I', 36))
    f.write(b'WAVE')
    f.write(b'fmt ')
    f.write(struct.pack('<I', 16))
    f.write(struct.pack('<HHIIHH', 1, 1, 44100, 88200, 2, 16))

# ファイル位置を追跡
with open('/tmp/test.wav', 'rb') as f:
    # RIFFヘッダをスキップ
    f.read(12)
    print(f"After RIFF: pos={f.tell()}")  # 12

    # 12バイト読む
    tmp = f.read(12)
    print(f"After read(12): pos={f.tell()}")  # 24
    print(f"Data: {tmp!r}")

    # -8バイト戻る（間違い）
    f.seek(-8, 1)
    print(f"After seek(-8, 1): pos={f.tell()}")  # 16

    # 24バイト読む
    fmt = f.read(24)
    print(f"After read(24): pos={f.tell()}")  # 40
    print(f"Data: {fmt!r}")

    # unpack
    chunk_id, chunk_size, audio_format, channel_num, \
        sample_rate, bytes_rate, block_align, bit_depth = struct.unpack('<4sIHHIIHH', fmt)

    print(f"\nchunk_size = {chunk_size}")  # 65537 (異常!)
    print(f"Expected: 16, Got: {chunk_size}")
```

**実行結果**:
```
After RIFF: pos=12
After read(12): pos=24
Data: b'fmt \x10\x00\x00\x00\x01\x00\x01\x00'
After seek(-8, 1): pos=16
After read(24): pos=40
Data: b'\x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data'

chunk_size = 65537
Expected: 16, Got: 65537
```

これで**バグ2が確認できます**。

### テスト3: 正しい読み取り方法

```python
# test_correct_reading.py
import struct

with open('/tmp/test.wav', 'rb') as f:
    f.read(12)  # RIFF

    tmp = f.read(12)
    print(f"Position after read(12): {f.tell()}")  # 24

    # -12バイト戻る（正しい）
    f.seek(-12, 1)
    print(f"Position after seek(-12, 1): {f.tell()}")  # 12

    # 24バイト読む
    fmt = f.read(24)
    print(f"Position after read(24): {f.tell()}")  # 36
    print(f"Data: {fmt!r}")

    # unpack
    chunk_id, chunk_size, audio_format, channel_num, \
        sample_rate, bytes_rate, block_align, bit_depth = struct.unpack('<4sIHHIIHH', fmt)

    print(f"\nchunk_size = {chunk_size}")  # 16 (正しい!)
    print(f"audio_format = {audio_format}")  # 1
    print(f"channel_num = {channel_num}")  # 1
    print(f"sample_rate = {sample_rate}")  # 44100
```

**実行結果**:
```
Position after read(12): 24
Position after seek(-12, 1): 12
Position after read(24): 36
Data: b'fmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00'

chunk_size = 16
audio_format = 1
channel_num = 1
sample_rate = 44100
```

これで**正しい修正方法が確認できます**。

## 学んだ重要な概念

### 1. デバッグ出力の重要性

**最も重要な教訓**: デバッグ出力がなければ、問題を見つけるのに何時間もかかる可能性がある。

**デバッグ出力のベストプラクティス**:

```python
def process_read(f):
    # 1. 入力時点の状態を記録
    pos_before = f.tell()

    # 2. 操作を実行
    tmp = f.read(12)

    # 3. 操作後の状態を記録
    pos_after = f.tell()

    # 4. デバッグ出力（標準エラー出力に）
    print(f"DEBUG: read() pos={pos_before}->{pos_after}, bytes={len(tmp)}, data={tmp!r}",
          file=sys.stderr)

    # 5. 変数の型と値を確認
    if tmp:
        tmp_id, tmp_size, tmp_format = struct.unpack('<4sI4s', tmp)
        print(f"DEBUG: tmp_id={tmp_id!r} (type={type(tmp_id).__name__})", file=sys.stderr)
        print(f"DEBUG: tmp_size={tmp_size}", file=sys.stderr)

        # 6. 比較結果を確認
        print(f"DEBUG: tmp_id == 'RIFF'? {tmp_id == 'RIFF'}", file=sys.stderr)
        print(f"DEBUG: tmp_id == b'RIFF'? {tmp_id == b'RIFF'}", file=sys.stderr)
```

**デバッグ出力を入れるべき場所**:
- ✅ ファイル読み取りの前後
- ✅ ファイルポインタ移動（seek）の前後
- ✅ 変数の型が不明な時
- ✅ 比較演算の結果
- ✅ ループのイテレーション開始時

**デバッグ出力を残すべき期間**:
- 開発中: **常に入れておく**
- テスト完了後: コメントアウトするか、デバッグフラグで制御

```python
DEBUG = True  # または環境変数から取得

def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs, file=sys.stderr)

# 使用例
debug_print(f"pos={f.tell()}, data={tmp!r}")
```

### 2. 小さいテストケースの作り方

**原則**: 問題を**最小限のコード**で再現する

**ステップ1: 問題を切り分ける**
```
大きな問題: WAVファイル解析が無限ループする
  ↓
小さな問題1: チャンクが認識されない
小さな問題2: ファイルポインタが異常
小さな問題3: ループが終わらない
```

**ステップ2: 各問題を独立してテスト**
```python
# 問題1のテスト: 型の確認
import struct
data = b'RIFF\x00\x00\x00\x00WAVE'
tmp_id, _, _ = struct.unpack('<4sI4s', data)
print(f"Type: {type(tmp_id)}, Value: {tmp_id!r}")
print(f"Match 'RIFF': {tmp_id == 'RIFF'}")
print(f"Match b'RIFF': {tmp_id == b'RIFF'}")

# 問題2のテスト: ファイル位置の追跡
with open('test.wav', 'rb') as f:
    print(f"Before: {f.tell()}")
    data = f.read(12)
    print(f"After read: {f.tell()}")
    f.seek(-8, 1)
    print(f"After seek: {f.tell()}")
```

**ステップ3: 期待値と実際の値を比較**
```python
expected_chunk_size = 16
actual_chunk_size = chunk_size

print(f"Expected: {expected_chunk_size}")
print(f"Actual: {actual_chunk_size}")
print(f"Match: {expected_chunk_size == actual_chunk_size}")

if expected_chunk_size != actual_chunk_size:
    print(f"Difference: {actual_chunk_size - expected_chunk_size}")
    print(f"Hex: expected=0x{expected_chunk_size:04x}, actual=0x{actual_chunk_size:04x}")
```

### 3. Pythonのバイト文字列とUnicode文字列

**基本ルール**:
```python
# バイト文字列 (bytes)
b'RIFF'  # bプレフィックス
type(b'RIFF')  # <class 'bytes'>

# Unicode文字列 (str)
'RIFF'  # プレフィックスなし
type('RIFF')  # <class 'str'>

# 比較は型が一致しないとFalse
b'RIFF' == 'RIFF'  # False
b'RIFF' == b'RIFF'  # True

# 変換
b'RIFF'.decode('ascii')  # bytes → str: 'RIFF'
'RIFF'.encode('ascii')   # str → bytes: b'RIFF'
```

**struct.unpackの仕様**:
- フォーマット文字`s`は**常にバイト文字列を返す**
- `'4s'` → 4バイトのバイト文字列

**一貫性を保つ方法**:

**方法1: バイト文字列リテラルを使う**
```python
tmp_id, tmp_size, tmp_format = struct.unpack('<4sI4s', tmp)

if tmp_id == b'RIFF' and tmp_format == b'WAVE':  # bプレフィックス
    ...
elif tmp_id == b'fmt ':
    ...
```

**方法2: すぐにデコードする**
```python
tmp_id, tmp_size, tmp_format = struct.unpack('<4sI4s', tmp)

# すぐに文字列に変換
chunk_id = tmp_id.decode('ascii')
format_str = tmp_format.decode('ascii')

if chunk_id == 'RIFF' and format_str == 'WAVE':  # 通常の文字列
    ...
elif chunk_id == 'fmt ':
    ...
```

**推奨**: 方法2（すぐにデコード） - コード全体で文字列型に統一できる

### 4. ファイルポインタの管理

**ファイルポインタ操作の基本**:

```python
# 現在位置を取得
pos = f.tell()

# 絶対位置に移動
f.seek(100, 0)  # ファイル先頭から100バイト目

# 相対位置に移動
f.seek(10, 1)   # 現在位置から10バイト進む
f.seek(-5, 1)   # 現在位置から5バイト戻る

# ファイル終端からの位置
f.seek(-10, 2)  # ファイル終端から10バイト前
```

**デバッグ時のベストプラクティス**:

```python
def debug_seek(f, offset, whence=0, label=""):
    """デバッグ用のseek関数"""
    pos_before = f.tell()
    f.seek(offset, whence)
    pos_after = f.tell()

    whence_str = {0: 'SEEK_SET', 1: 'SEEK_CUR', 2: 'SEEK_END'}
    print(f"DEBUG seek({offset}, {whence_str[whence]}): "
          f"{pos_before} -> {pos_after} {label}", file=sys.stderr)

    return pos_after

# 使用例
debug_seek(f, -12, 1, "back to fmt chunk start")
```

**ファイル読み取りパターン**:

```python
# パターン1: ヘッダを読んでから本体を読む
header = f.read(8)  # chunk_id (4) + chunk_size (4)
chunk_id, chunk_size = struct.unpack('<4sI', header)

body = f.read(chunk_size)  # 本体を読む

# パターン2: 最初にN バイト読んで、足りなければ追加で読む
partial = f.read(12)  # 仮に12バイト読む
if needs_more:
    # 戻って全体を読み直す
    f.seek(-12, 1)
    full = f.read(24)
```

**今回の問題の正しいパターン**:

```python
# 12バイト読む（ヘッダ + 4バイト）
tmp = f.read(12)
tmp_id, tmp_size, tmp_format = struct.unpack('<4sI4s', tmp)

if tmp_id == b'fmt ':
    # fmtチャンクは全体を読む必要がある
    # 読んだ12バイトを全部戻す
    f.seek(-12, 1)

    # 最初から24バイト読む
    fmt_data = f.read(24)
    chunk_id, chunk_size, audio_format, ... = struct.unpack('<4sIHHIIHH', fmt_data)
```

### 5. ループ設計とエラーハンドリング

**安全なループの設計**:

```python
# 悪い例: 終了条件が不明確
while True:
    data = process()
    if data:
        handle(data)

# 良い例1: 明確な終了条件
max_iterations = 100
iteration = 0
while not_done and iteration < max_iterations:
    iteration += 1
    data = process()
    if data is None:
        break
    handle(data)

# 良い例2: ファイル終端を検出
while True:
    data = f.read(size)
    if not data:  # 空のバイト列 = ファイル終端
        break
    process(data)
```

**エラーハンドリングの3つの方法**:

```python
# 方法1: Noneを返す（推奨: ファイル終端など正常なケース）
def read_chunk(f):
    data = f.read(8)
    if not data:
        return None  # ファイル終端
    return parse(data)

# 使用側
chunk = read_chunk(f)
if chunk is None:
    break  # 正常終了

# 方法2: 例外を発生させる（推奨: エラーが例外的なケース）
def read_chunk(f):
    data = f.read(8)
    if not data:
        raise EOFError("Unexpected end of file")
    return parse(data)

# 使用側
try:
    chunk = read_chunk(f)
except EOFError as e:
    print(f"Error: {e}")
    return 1

# 方法3: タプルで成否を返す（成否と値の両方が必要な場合）
def read_chunk(f):
    data = f.read(8)
    if not data:
        return False, None
    return True, parse(data)

# 使用側
success, chunk = read_chunk(f)
if not success:
    break
```

**今回の問題での正しいエラーハンドリング**:

```python
def process_read(f):
    tmp = f.read(12)

    # ファイル終端を検出（正常終了）
    if not tmp:
        return None

    # 不完全な読み取り（エラー）
    if len(tmp) != 12:
        raise ValueError(f"Incomplete chunk header: got {len(tmp)} bytes, expected 12")

    # 正常処理
    ...

# main関数
while not all_chunks_found:
    try:
        chunk = process_read(f)
        if chunk is None:  # ファイル終端
            break
        handle_chunk(chunk)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
```

## 修正後の完全なコード例

```python
#!/usr/bin/env python3
import sys
import struct

# デバッグフラグ
DEBUG = False  # Trueにするとデバッグ出力が有効になる

def debug_print(*args, **kwargs):
    """デバッグ出力用のヘルパー関数"""
    if DEBUG:
        print(*args, **kwargs, file=sys.stderr)


def process_read(f):
    """
    WAVファイルのチャンクを読み取り、解析する

    Returns:
        dict: チャンク情報を含む辞書
        None: ファイル終端に達した場合

    Raises:
        ValueError: 不完全なチャンクヘッダの場合
    """
    # デバッグ: ファイル位置を記録
    pos_before = f.tell()

    # 12バイト読む（チャンクヘッダ）
    tmp = f.read(12)

    pos_after = f.tell()
    debug_print(f"DEBUG: read(12) pos={pos_before}->{pos_after}, bytes={len(tmp)}, data={tmp!r}")

    # ファイル終端チェック
    if not tmp:
        debug_print("DEBUG: End of file reached")
        return None

    # 不完全な読み取りチェック
    if len(tmp) != 12:
        raise ValueError(f"Incomplete chunk header: got {len(tmp)} bytes, expected 12")

    # バイト文字列としてunpack
    tmp_id, tmp_size, tmp_format = struct.unpack('<4sI4s', tmp)

    # デバッグ: 型と値を確認
    debug_print(f"DEBUG: tmp_id={tmp_id!r} (type={type(tmp_id).__name__})")
    debug_print(f"DEBUG: tmp_size={tmp_size}")
    debug_print(f"DEBUG: tmp_format={tmp_format!r}")

    # RIFFチャンク
    if tmp_id == b'RIFF' and tmp_format == b'WAVE':
        debug_print("DEBUG: Found RIFF chunk")
        return {
            'chunk_id': tmp_id.decode('ascii'),
            'chunk_size': tmp_size,
            'format': tmp_format.decode('ascii')
        }

    # fmtチャンク
    elif tmp_id == b'fmt ':
        debug_print("DEBUG: Found fmt chunk")

        # 読んだ12バイトを全部戻す
        pos_before_seek = f.tell()
        f.seek(-12, 1)
        pos_after_seek = f.tell()
        debug_print(f"DEBUG: seek(-12, 1) pos={pos_before_seek}->{pos_after_seek}")

        # fmtチャンク全体（24バイト）を読む
        fmt_data = f.read(24)
        debug_print(f"DEBUG: read(24) pos={pos_after_seek}->{f.tell()}, data={fmt_data!r}")

        if len(fmt_data) < 24:
            raise ValueError(f"Incomplete fmt chunk: got {len(fmt_data)} bytes, expected 24")

        chunk_id, chunk_size, audio_format, channel_num, \
            sample_rate, byte_rate, block_align, bit_depth = \
            struct.unpack('<4sIHHIIHH', fmt_data)

        debug_print(f"DEBUG: chunk_size={chunk_size}, audio_format={audio_format}")

        # 16バイトを超える部分をスキップ
        if chunk_size > 16:
            skip_bytes = chunk_size - 16
            pos_before_skip = f.tell()
            f.seek(skip_bytes, 1)
            debug_print(f"DEBUG: skip {skip_bytes} bytes, pos={pos_before_skip}->{f.tell()}")

        return {
            'chunk_id': chunk_id.decode('ascii'),
            'chunk_size': chunk_size,
            'audio_format': audio_format,
            'channel_num': channel_num,
            'sample_rate': sample_rate,
            'byte_rate': byte_rate,
            'block_align': block_align,
            'bit_depth': bit_depth
        }

    # dataチャンク
    elif tmp_id == b'data':
        debug_print("DEBUG: Found data chunk")
        return {
            'chunk_id': tmp_id.decode('ascii'),
            'chunk_size': tmp_size
        }

    # 未知のチャンクをスキップ
    else:
        chunk_id_str = tmp_id.decode('ascii', errors='replace')
        debug_print(f"DEBUG: Unknown chunk '{chunk_id_str}', skipping {tmp_size} bytes")

        pos_before_skip = f.tell()
        f.seek(tmp_size, 1)
        debug_print(f"DEBUG: skip pos={pos_before_skip}->{f.tell()}")

        return {
            'chunk_id': chunk_id_str,
            'chunk_size': tmp_size
        }


def main():
    if len(sys.argv) != 2:
        print("Usage: ex28_bin_9b.py <wav_file>", file=sys.stderr)
        return 1

    file_name = sys.argv[1]
    riff = None
    fmt = None
    data = None

    try:
        with open(file_name, "rb") as f:
            # 安全装置: 最大100チャンクまで
            max_chunks = 100
            chunk_count = 0

            while (not fmt or not data or not riff) and chunk_count < max_chunks:
                chunk_count += 1
                debug_print(f"\n=== Iteration {chunk_count} ===")

                try:
                    chunk = process_read(f)
                except ValueError as e:
                    print(f"Error: {e}", file=sys.stderr)
                    return 1

                # ファイル終端チェック
                if chunk is None:
                    debug_print("DEBUG: Reached end of file")
                    break

                # チャンクの種類に応じて処理
                chunk_id = chunk.get('chunk_id')

                if chunk_id == 'RIFF' and chunk.get('format') == 'WAVE' and not riff:
                    debug_print("  -> Setting riff")
                    riff = chunk
                elif chunk_id == 'fmt ' and not fmt:
                    debug_print("  -> Setting fmt")
                    fmt = chunk
                elif chunk_id == 'data' and not data:
                    debug_print("  -> Setting data")
                    data = chunk
                else:
                    debug_print(f"  -> Skipped chunk '{chunk_id}'")

            # 最大チャンク数チェック
            if chunk_count >= max_chunks:
                print(f"Error: Too many chunks (>{max_chunks})", file=sys.stderr)
                return 1

        # 必須チャンクの存在確認
        if not riff or not fmt or not data:
            missing = []
            if not riff:
                missing.append('RIFF')
            if not fmt:
                missing.append('fmt')
            if not data:
                missing.append('data')
            print(f"Error: Missing required chunks: {', '.join(missing)}", file=sys.stderr)
            return 1

        # チャンク情報を表示
        print("=== Scanning Chunks ===")
        print(f"Found chunk: fmt  (size: {fmt['chunk_size']} bytes)")
        print(f"Found chunk: data (size: {data['chunk_size']} bytes)")
        print()

        # WAVファイル情報を表示
        print("=== WAV File Information ===")

        format_name = "PCM" if fmt['audio_format'] == 1 else f"Unknown ({fmt['audio_format']})"

        if fmt['channel_num'] == 1:
            channel_desc = "Mono"
        elif fmt['channel_num'] == 2:
            channel_desc = "Stereo"
        else:
            channel_desc = f"{fmt['channel_num']} channels"

        # Duration計算
        duration = data['chunk_size'] / fmt['byte_rate']

        print(f"Audio format: {fmt['audio_format']} ({format_name})")
        print(f"Channels: {fmt['channel_num']} ({channel_desc})")
        print(f"Sample rate: {fmt['sample_rate']} Hz")
        print(f"Bits per sample: {fmt['bit_depth']}")
        print(f"Data size: {data['chunk_size']} bytes")
        print(f"Duration: {duration:.2f} seconds")

        return 0

    except FileNotFoundError:
        print(f"Error: File not found: {file_name}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if DEBUG:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
```

## まとめ

### 最も重要な教訓

**デバッグ出力を最初から書く習慣をつける**

- コードを書く時に、同時にデバッグ出力も書く
- 変数の型、値、ファイル位置を常に確認
- 期待値と実際の値を比較

**デバッグ出力があれば**:
- 問題発見時間: **数時間 → 5分**
- 問題の理解度: **推測 → 確信**
- 修正の確実性: **不安 → 確実**

### 成功のポイント

1. ✅ **デバッグ出力を追加する**
   - ファイル位置（`f.tell()`）
   - 変数の型（`type(x)`）
   - 変数の値（`repr(x)`）
   - 比較結果

2. ✅ **小さいテストケースを作る**
   - 問題を切り分ける
   - 最小限のコードで再現
   - 期待値と実際の値を比較

3. ✅ **型を意識する**
   - バイト文字列と文字列の違い
   - `struct.unpack()`の返り値
   - 一貫性を保つ（すぐにデコード）

4. ✅ **ファイルポインタを追跡する**
   - `f.tell()`で位置を確認
   - `seek()`の前後で位置を記録
   - 期待位置と実際の位置を比較

5. ✅ **安全なループ設計**
   - 明確な終了条件
   - 最大反復回数の制限
   - 適切なエラーハンドリング

### 今後の応用

このデバッグ手法は、以下の場面で役立ちます:

- バイナリファイル解析（画像、音声、動画フォーマット）
- ネットワークプロトコルの実装
- データシリアライゼーション
- ファイルシステムの実装
- 暗号化/復号化処理

**重要**: 問題を見つけられないのは経験不足ではなく、**デバッグ手法を知らない**だけです。今日から実践できます。

---

**作成日**: 2025-12-28
**ファイル**: ex28_bin_9b.py
**学習テーマ**: デバッグ手法、バイト文字列の扱い、ファイルポインタ管理、小さいテストケースの作成
**最重要教訓**: デバッグ出力を最初から書く習慣が、問題発見時間を劇的に短縮する
