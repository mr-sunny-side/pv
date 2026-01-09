# ex23_csv_output.py 修正提案

日付: 2025-11-16

## 現状の問題点

現在のコードでは、リストの長さが不整合になる可能性があります（99-101行目のコメント参照）:

### 1. ext_sender_to関数（32-35行目）
- 三項演算子を使用
- `re.search`が失敗すると`None`を返し、`list_sender`が呼ばれない
- → `sender_list`に何も追加されない

```python
def ext_sender_to(line):
    if line:
        matched = re.search(r"[\w\.-]+@[\w\.-]+", line)
        return matched and list_sender(matched.group())
```

### 2. ext_domain_to関数（37-44行目）
- `IndexError`をキャッチしている
- エラー時に`line`をそのまま`list_domain`に渡している
- **問題**: `line`全体（例: "sender@domain.com"）がドメインリストに追加されてしまう

```python
def ext_domain_to(line):
    if line:
        try:
            domain = line.split("@")[1]
            return list_domain(domain)
        except IndexError:
            print(f"couldn't split line: {line}")
            return list_domain(line)  # ← line全体が入ってしまう
```

---

## 提案された修正内容

### ext_sender_to関数の修正

**修正方針**: 三項演算子をやめて、if文で記述。`re.search`が失敗した場合にそのまま`line`を`list_sender`に渡す。

**修正後のコード**:
```python
def ext_sender_to(line):
    if line:
        matched = re.search(r"[\w\.-]+@[\w\.-]+", line)
        if matched:
            return list_sender(matched.group())
        else:
            # 正規表現マッチ失敗時、元のlineを保存してリスト不整合を防ぐ
            return list_sender(line)
    return None
```

**メリット**:
- リストの不整合を防げる
- 可読性が向上
- デバッグしやすい

---

### ext_domain_to関数の修正

**現状の問題点**:
- `line`をそのまま渡すと、`@`を含む完全なメールアドレスがドメインリストに入ってしまう
- `ext_sender_to`で既に正規表現マッチに失敗している場合、その`line`には有効なメールアドレスがない可能性が高い
- その場合、`split("@")`も失敗する
- `line`をドメインとして保存すると、データの整合性が低下する

**修正案（3つの選択肢）**:

#### A案: 空文字列を追加
```python
def ext_domain_to(line):
    if line:
        try:
            domain = line.split("@")[1]
            return list_domain(domain)
        except IndexError:
            print(f"couldn't split line: {line}")
            return list_domain("")  # 空文字列を追加
    return None
```

**メリット**:
- リスト長は保たれる
- エラー行が明確（空文字列）
- CSV出力時に空欄として表示される

**デメリット**:
- 元のデータが失われる

---

#### B案: line全体を追加（現状維持）
```python
def ext_domain_to(line):
    if line:
        try:
            domain = line.split("@")[1]
            return list_domain(domain)
        except IndexError:
            print(f"couldn't split line: {line}")
            return list_domain(line)  # line全体を追加
    return None
```

**メリット**:
- 元のデータが残る
- 後で確認・修正が可能

**デメリット**:
- ドメインとして不適切なデータが入る
- データの整合性が低い

---

#### C案: プレースホルダーを追加
```python
def ext_domain_to(line):
    if line:
        try:
            domain = line.split("@")[1]
            return list_domain(domain)
        except IndexError:
            print(f"couldn't split line: {line}")
            return list_domain("PARSE_ERROR")  # エラー表示
    return None
```

**メリット**:
- エラーが明確に識別できる
- リスト長は保たれる
- CSV出力時に問題行を見つけやすい

**デメリット**:
- 元のデータが失われる

---

## 推奨案

**ext_sender_to関数**: 提案通りif文化し、マッチ失敗時は`line`を保存

**ext_domain_to関数**: **C案（プレースホルダー）** を推奨
- 理由1: エラー行を明確に識別できる
- 理由2: CSVファイルを見たときに問題箇所が一目瞭然
- 理由3: 元のlineはコンソール出力（`print`）で確認可能

---

## 実装例（推奨案）

```python
def ext_sender_to(line):
    if line:
        matched = re.search(r"[\w\.-]+@[\w\.-]+", line)
        if matched:
            return list_sender(matched.group())
        else:
            # 正規表現マッチ失敗時、元のlineを保存
            return list_sender(line)
    return None

def ext_domain_to(line):
    if line:
        try:
            domain = line.split("@")[1]
            return list_domain(domain)
        except IndexError:
            print(f"couldn't split line: {line}")
            return list_domain("PARSE_ERROR")
    return None
```

---

## 次のステップ

1. どの修正案（A, B, C）を採用するか決定
2. コードを修正
3. テストデータで動作確認
4. CSV出力結果を確認
