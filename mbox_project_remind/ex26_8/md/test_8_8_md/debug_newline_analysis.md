# 改行問題のデバッグ方法

## 観察された問題

出力ファイル `test_case/txt/test_8_8_py.txt` において、特定の行で意図しない改行が発生している:

```
13→freeeサポート
14→no-reply@service.muumuu-domain.com\r               ->              service.muumuu-domain.com
```

13行目は「freeeサポート」のみで、ドメインが出力されていない（改行されている）

## 原因の仮説

1. **`\r` (キャリッジリターン) の存在**: 多くの行末に `\r` が見える
2. **エンコードされた名前と `@` の判定**: `@` が含まれていない → デコードして出力 → continue
3. **Windows改行コードの混在**: `\r\n` が混在している可能性

## デバッグ方法

### 方法1: `cat -A` で制御文字を可視化（行数制限付き）

```bash
# 最初の20行だけ表示
cat -A test_case/txt/test_8_8_py.txt | head -20

# 13-15行目だけ表示
cat -A test_case/txt/test_8_8_py.txt | sed -n '13,15p'

# "freee" を含む行の前後3行を表示
cat -A test_case/txt/test_8_8_py.txt | grep -A 3 -B 3 "freee"
```

**`cat -A` の記号**:
- `$` : 改行 (`\n`)
- `^M` : キャリッジリターン (`\r`)
- `^I` : タブ (`\t`)

### 方法2: `od` (octal dump) でバイナリレベル確認

```bash
# 13行目付近のバイト列を16進数で表示
sed -n '13,15p' test_case/txt/test_8_8_py.txt | od -A x -t x1z -v

# より読みやすく
sed -n '13,15p' test_case/txt/test_8_8_py.txt | hexdump -C
```

**重要なバイト**:
- `0a` : `\n` (LF - Unix改行)
- `0d` : `\r` (CR - Windows改行の一部)
- `0d 0a` : `\r\n` (Windows改行)

### 方法3: Python で中間データをデバッグ

`ext_sender_file` の出力を直接確認:

```bash
# ext_senderの出力を最初の20行だけ取得
$C_FILE/ex26_8_7_file $MBOX/google.mbox | head -20 | cat -A

# "freee" を含む行の前後を確認
$C_FILE/ex26_8_7_file $MBOX/google.mbox | grep -A 2 -B 2 "freee" | cat -A
```

### 方法4: Python デバッグスクリプトを作成

より詳細な分析のために、専用のデバッグスクリプトを作成:

```python
# debug_sender_list.py
import subprocess
import sys

ext_sender_file = sys.argv[1]
mbox = sys.argv[2]

result = subprocess.run(
    [ext_sender_file, mbox],
    capture_output=True,
    check=True
)

sender_list = result.stdout.strip().split(b'\n')

print(f"Total entries: {len(sender_list)}\n")

# 最初の20エントリを詳細表示
for i, raw_email in enumerate(sender_list[:20]):
    has_at = b'@' in raw_email
    repr_str = repr(raw_email)
    decoded = raw_email.decode('utf-8', errors='replace')

    print(f"[{i:3d}] has_@: {has_at}")
    print(f"      repr : {repr_str}")
    print(f"      text : {decoded}")
    print()

# "freee" を含むエントリを検索
print("\n=== Entries containing 'freee' ===")
for i, raw_email in enumerate(sender_list):
    if b'freee' in raw_email.lower():
        print(f"[{i:3d}] {repr(raw_email)}")
        print(f"      {raw_email.decode('utf-8', errors='replace')}")
```

実行:
```bash
python3 debug_sender_list.py $C_FILE/ex26_8_7_file $MBOX/google.mbox
```

## 予想される問題と解決策

### 問題1: メールアドレスに `\r` が含まれる

**原因**: C言語の `ext_email_and_copy()` が `\n` で終端を探すため、`\r\n` の場合は `\r` が含まれる

**解決策**: Python側で `\r` を除去

```python
# sender_list作成時
sender_list = result.stdout.strip().replace(b'\r', b'').split(b'\n')
```

または

```python
# ループ内で個別に処理
raw_email = raw_email.strip()  # \r\n の両方を除去
```

### 問題2: エンコードされた名前に `@` が含まれていない

**原因**: `=?UTF-8?B?ZnJlZWXjgrXjg53jg7zjg4g=?=` のような形式には `@` がない

**現在の処理**:
```python
if raw_email and b'@' not in raw_email:
    # デコードして出力
    print(decode_sender)
    continue
```

これは正しい動作。ただし、ドメイン情報がない名前だけのエントリの場合、改行だけが出力される。

### 問題3: 空の decode_sender

`safe_decode()` が `None` を返す場合、何も出力されずに次のループへ進むため、空行が生まれる可能性がある。

**改善案**:
```python
if decode_sender:
    print(decode_sender)
else:
    print(f"(Decode failed: {raw_email[:50]})", file=sys.stderr)
```

## 推奨デバッグ手順

1. **まず `cat -A` で制御文字を確認**
   ```bash
   cat -A test_case/txt/test_8_8_py.txt | grep -A 2 -B 2 "freee"
   ```

2. **ext_senderの出力を確認**
   ```bash
   $C_FILE/ex26_8_7_file $MBOX/google.mbox | grep -A 2 -B 2 "freee" | cat -A
   ```

3. **Python デバッグスクリプトで詳細分析**
   上記の `debug_sender_list.py` を使用

4. **問題を特定したら修正を適用**
