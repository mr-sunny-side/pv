# ex25_2_process_all.py 備忘録

## `mailbox` と `email` の違い

### mailbox モジュール
- **mboxファイル全体**を扱うコンテナ
- `mailbox.mbox(file_name)` で mbox ファイルを開くと、**複数のメッセージを格納したコレクション**が得られる
- `for msg in mbox:` で各メッセージ（emailオブジェクト）を1つずつ取り出せる

### email モジュール
- **個々のメールメッセージ**を表すオブジェクト
- ヘッダー（From, To等）やボディにアクセスできる

---

## コードの問題点

### 1. ループ内で取り出したメッセージを使っていない（最重要）

```python
# ❌ 間違い
for idx, mails in enumerate(mbox, 1):
    bool_rcpt = is_for_rcpt(mbox["to"])   # mbox全体を参照
    sender = ext_sender(mbox["from"])     # mbox全体を参照

# ✅ 正しい
for idx, mail in enumerate(mbox, 1):
    bool_rcpt = is_for_rcpt(mail["to"])   # 個別メッセージを参照
    sender = ext_sender(mail["from"])     # 個別メッセージを参照
```

### 2. 不要な `with open()`（75行目）
`mailbox.mbox()` が既にファイルを開いているので不要

### 3. dict_domain関数のバグ（15行目）

```python
# ❌ 間違い
domains_dict[domain] = domains_dict[domain].get(domain, 0) + 1

# ✅ 正しい
domains_dict[domain] = domains_dict.get(domain, 0) + 1
```

### 4. print_result関数のバグ（62行目）

```python
# ❌ 間違い（sorted()の結果はリスト、dictではない）
for domain, count in sorted_domains.items():

# ✅ 正しい
for domain, count in sorted_domains:
```

### 5. time_monitor関数が None を返す問題（42行目）

条件分岐で `return` がない場合、Pythonは暗黙的に `None` を返す。
それが `last_time` に代入され、次のループで `None - float` のエラーになる。

```python
# ❌ 間違い
def time_monitor(current_time, last_time, start_time, idx):
    if current_time - last_time >= 0.1:
        ...
        return current_time
    # 条件外では何も返さない → None

# ✅ 正しい
def time_monitor(current_time, last_time, start_time, idx):
    if current_time - last_time >= 0.1:
        elapsed = current_time - start_time
        print(f"Processing... mail {idx}: {elapsed:.1f}s", end='\r', flush=True)
        return current_time
    return last_time  # 条件外では元の値を返す
```

**注意**: `idx` も引数として渡す必要がある（関数スコープ外の変数だから）

### 6. f-string内での型変換（66行目）

Pythonでは異なる型同士を `+` で連結できない。整数 `i` と文字列 `'.'` を連結するには `str()` で型変換が必要。

```python
# ❌ エラー（int + str はできない）
i + '.'      # TypeError: unsupported operand type(s) for +: 'int' and 'str'

# ✅ 方法1: str()で明示的に変換
str(i) + '.'

# ✅ 方法2: f-stringで別々に書く（シンプルで推奨）
print(f"{i}. {domain:<50}: {count:>10} times")
```

**機序**:
- Pythonは「暗黙の型変換」をしない言語
- `+` 演算子は両辺が同じ型である必要がある
- f-string の `{}` 内では自動的に `str()` が適用されるが、`{}` 内で `+` を使う場合は手動で変換が必要

### 7. キャリッジリターン `\r` による表示残り問題

`end='\r'` を使うと行頭に戻るが改行しない。次の出力が短いと前の文字列の末尾が残る。

```
# 実際の出力例
100 mails completed: 0.6s6s   ← 末尾の「6s」が前の行から残っている
```

**機序**:
1. `time_monitor`: `Processing... mail 99: 0.6s` を出力（`\r` で行頭に戻る、改行なし）
2. `progress_monitor`: `100 mails completed: 0.6s` を上書き出力
3. 前の文字列の方が長いと、上書きされなかった末尾が残る

**解決方法**: スペースで残りを消す
```python
print(f"\r{idx} mails completed: {prog_time:.1f}s" + " " * 20)
```

---

## 補足: f-string の書式指定

### `:.1f` の意味
- `:` = 書式指定の開始
- `.1` = 小数点以下1桁
- `f` = 浮動小数点数（float）として表示

```python
x = 3.14159
print(f"{x:.1f}")   # → 3.1
print(f"{x:.2f}")   # → 3.14
print(f"{x:.0f}")   # → 3
```

### その他の書式指定
```python
print(f"{text:<10}")   # 左寄せ、幅10
print(f"{text:>10}")   # 右寄せ、幅10
print(f"{num:05d}")    # ゼロ埋め5桁（整数）
```
