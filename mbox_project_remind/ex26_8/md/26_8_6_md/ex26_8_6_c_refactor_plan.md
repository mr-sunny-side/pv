# Plan: C言語版のメール抽出ロジックをPython版と統一

**日付**: 2024-12-10
**対象ファイル**: ex26_8_6.c
**目的**: Python版と同じメール抽出ロジックに統一し、CPU時間を正確に比較する

---

## タスク概要

ex26_8_6.c のメール抽出ロジックを、Python版 (ex26_8_6.py) と同じ方式に変更する。
具体的には、正規表現パターン `[\w.-]+@[\w.-]+` と同等の処理を C言語で実装する。

---

## 現在のロジックの問題点

### C言語版 (ex26_8_6.c:18-41)
```c
int ext_sender_and_copy(char *from_line, char **email)
{
    // <email@example.com> 形式を優先
    if ((start = strchr(from_line, '<')) != NULL) { ... }
    // スペース区切りを次点とする
    else if ((start = strchr(from_line, ' ')) != NULL) { ... }
}
```

**特徴**:
- `<>` で囲まれたメールアドレスを優先的に抽出
- `<>` がない場合はスペース以降を抽出
- 特定の形式に依存したパース

### Python版 (ex26_8_6.py:28-32)
```python
def ext_sender(from_line):
    email = re.search(r"[\w.-]+@[\w.-]+", from_line)
    return email.group() if email else None
```

**特徴**:
- `@` を含むパターンを直接検索
- 形式に依存しない汎用的なマッチング
- 正規表現による柔軟な抽出

### 差異

C言語版は `<>` やスペースを基準にパースするが、Python版は `@` を含むパターンを直接検索する。
この違いにより、CPU時間比較が不正確になる可能性がある。

---

## 実装方針

### 選択肢1: 手動パターンマッチング（推奨）
- **メリット**:
  - 外部ライブラリ不要
  - シンプルで理解しやすい
  - 学習に最適
  - デバッグが容易
- **デメリット**:
  - 正規表現ほど柔軟ではない
  - 複雑なパターンには対応しづらい
- **実装方法**:
  - `strchr()` で `@` を探す
  - `@` の前後を解析してメールアドレスを抽出

### 選択肢2: POSIX正規表現 (regex.h)
- **メリット**:
  - 正規表現が使える
  - 標準ライブラリの一部（多くのシステムで利用可能）
- **デメリット**:
  - `\w` が使えない（POSIX EREでは `[[:alnum:]_]` を使用）
  - 実装が複雑
  - エラーハンドリングが必要
- **実装方法**:
  ```c
  #include <regex.h>
  regex_t regex;
  regcomp(&regex, "[[:alnum:].-]+@[[:alnum:].-]+", REG_EXTENDED);
  ```

### 選択肢3: PCRE ライブラリ
- **メリット**:
  - 完全な正規表現サポート
  - Pythonの `re` モジュールと同等の機能
- **デメリット**:
  - 外部ライブラリが必要（インストールが必要）
  - 学習目的には過剰
  - 依存関係が増える

---

## 推奨実装（選択肢1）

### 新しい `ext_sender_and_copy` 関数の設計

#### アルゴリズム

1. **`@` を探す**: `strchr(from_line, '@')` で位置を特定
2. **前方向に展開**: `@` の左側から英数字・ドット・ハイフン・アンダースコアを収集
3. **後方向に展開**: `@` の右側から英数字・ドット・ハイフン・アンダースコアを収集
4. **メモリ確保**: 抽出した文字列を動的に確保してコピー

#### 実装ステップ

1. **ヘルパー関数の追加**
   ```c
   int is_email_char(char c)
   {
       return (isalnum(c) || c == '.' || c == '-' || c == '_');
   }
   ```
   - `isalnum()`: 英数字（`[a-zA-Z0-9]`）をチェック
   - `c == '.'`: ドット
   - `c == '-'`: ハイフン
   - `c == '_'`: アンダースコア
   - Python の `\w` は `[a-zA-Z0-9_]` なので、`_` も含める

2. **ext_sender_and_copy の書き換え**
   - `@` を検索
   - 前後に展開してメールアドレスの開始・終了位置を特定
   - `malloc` + `strncpy` で抽出

3. **エッジケースの処理**
   - `@` が存在しない場合 → `-1` を返す
   - `@` の前後に有効な文字がない場合 → `-1` を返す
   - `malloc` 失敗 → `1` を返す

---

## 実装の詳細コード例

```c
#include <ctype.h>  // isalnum() のために追加

// ヘルパー関数: メールアドレスに使える文字かチェック
int is_email_char(char c)
{
    return (isalnum(c) || c == '.' || c == '-' || c == '_');
}

// 新しい実装
int ext_sender_and_copy(char *from_line, char **email)
{
    char *at_sign = strchr(from_line, '@');
    if (at_sign == NULL)
        return -1;  // @ が見つからない

    // @ の左側の開始位置を探す
    char *start = at_sign - 1;
    while (start >= from_line && is_email_char(*start))
        start--;
    start++;  // 1文字戻る（有効な文字の開始位置）

    // @ の右側の終了位置を探す
    char *end = at_sign + 1;
    while (*end != '\0' && is_email_char(*end))
        end++;

    // 有効なメールアドレスかチェック
    // start >= at_sign: @ の左側に文字がない
    // end <= at_sign + 1: @ の右側に文字がない
    if (start >= at_sign || end <= at_sign + 1)
        return -1;

    // メモリ確保とコピー
    int len = end - start;
    *email = malloc(len + 1);
    if (*email == NULL)
        return 1;  // malloc失敗

    strncpy(*email, start, len);
    (*email)[len] = '\0';
    return 0;
}
```

### コードの解説

#### ポインタ操作のポイント

1. **`start` の初期化**
   ```c
   char *start = at_sign - 1;
   ```
   - `@` の1文字前から探索開始

2. **後退しながら探索**
   ```c
   while (start >= from_line && is_email_char(*start))
       start--;
   ```
   - `start >= from_line`: 文字列の先頭を超えないようにチェック
   - `is_email_char(*start)`: 有効な文字かチェック
   - ループ終了時、`start` は**無効な文字の位置**を指す

3. **1文字進める**
   ```c
   start++;
   ```
   - 無効な文字の次（有効な文字の開始位置）に調整

4. **`end` の探索**
   ```c
   char *end = at_sign + 1;
   while (*end != '\0' && is_email_char(*end))
       end++;
   ```
   - `@` の1文字後から探索開始
   - ループ終了時、`end` は**無効な文字または終端の位置**を指す

5. **長さの計算**
   ```c
   int len = end - start;
   ```
   - ポインタの差分で文字列の長さを計算

---

## テスト項目

修正後、以下のパターンでテストする：

| 入力 | 期待される出力 | 説明 |
|------|---------------|------|
| `From: user@example.com` | `user@example.com` | 基本形 |
| `From: <user@example.com>` | `user@example.com` | `<>` で囲まれたパターン |
| `From: John Doe <john.doe@example.com>` | `john.doe@example.com` | 名前 + `<>` パターン |
| `From: invalid-line` | エラー（抽出失敗） | `@` がない |
| `From: @example.com` | エラー（抽出失敗） | `@` の左側が空 |
| `From: user@` | エラー（抽出失敗） | `@` の右側が空 |

---

## 実装ファイル

- **修正対象**: `/home/namae/pv/mbox_project_remind/ex26_8/ex26_8_6.c`
- **修正箇所**:
  - `ext_sender_and_copy` 関数 (18-41行目)
- **追加要素**:
  - `is_email_char` 関数（新規）
  - `#include <ctype.h>`（ファイル冒頭に追加）

### 修正前後の比較

#### 修正前
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

int ext_sender_and_copy(char *from_line, char **email)
{
    char *start = NULL;
    char *end = NULL;

    if ((start = strchr(from_line, '<')) != NULL) {
        start++;
        if ((end = strchr(from_line, '>')) == NULL)
            return -1;
    } else if ((start = strchr(from_line, ' ')) != NULL) {
        start++;
        if ((end = strchr(from_line, '\n')) == NULL)
            return -1;
    } else
        return -1;

    int interval = end - start;
    *email = malloc(interval + 1);
    if (*email == NULL)
        return 1;
    strncpy(*email, start, interval);
    (*email)[interval] = '\0';
    return 0;
}
```

#### 修正後
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <ctype.h>  // 追加

int is_email_char(char c)  // 新規追加
{
    return (isalnum(c) || c == '.' || c == '-' || c == '_');
}

int ext_sender_and_copy(char *from_line, char **email)
{
    char *at_sign = strchr(from_line, '@');
    if (at_sign == NULL)
        return -1;

    char *start = at_sign - 1;
    while (start >= from_line && is_email_char(*start))
        start--;
    start++;

    char *end = at_sign + 1;
    while (*end != '\0' && is_email_char(*end))
        end++;

    if (start >= at_sign || end <= at_sign + 1)
        return -1;

    int len = end - start;
    *email = malloc(len + 1);
    if (*email == NULL)
        return 1;

    strncpy(*email, start, len);
    (*email)[len] = '\0';
    return 0;
}
```

---

## 実装後の検証

### 1. コンパイル
```bash
cd /home/namae/pv/mbox_project_remind/ex26_8
42cc ex26_8_6.c -o ../test_case/out/ex26_8_6_file
```

**確認ポイント**:
- コンパイルエラーがないか
- 警告（Warning）が出ていないか

### 2. 実行
```bash
mbox_ex ../test_case/out/ex26_8_6_file
```

**確認ポイント**:
- プログラムが正常終了するか
- メールアドレスが正しく抽出されているか
- 出力ファイル `test_case/txt/ex26_8_6.txt` が生成されているか

### 3. Python版と出力を比較
```bash
diff test_case/txt/ex26_8_6.txt test_case/txt/ex26_8_6_py.txt
```

**期待される結果**:
- 差分がない（同じ出力）
- または、抽出されたメールアドレスが同じ

### 4. メモリリークチェック
```bash
c_valling ../test_case/out/ex26_8_6_file ../mbox/google.mbox > /dev/null
```

**確認ポイント**:
- `All heap blocks were freed` が表示されるか
- メモリリークがないか

### 5. CPU時間の比較
C言語版とPython版の処理時間を比較

```bash
# C言語版の実行
mbox_ex ../test_case/out/ex26_8_6_file

# Python版の実行
mbox_py_ex ex26_8_6.py
```

**確認ポイント**:
- どちらが速いか
- 処理時間の差（秒単位）

---

## まとめ

### 変更のメリット

1. **ロジックの統一**: C言語版とPython版で同じ抽出ロジックを使用
2. **正確な比較**: CPU時間を正確に比較できる
3. **学習効果**: ポインタ操作と文字列処理の理解が深まる
4. **汎用性**: `<>` などの特定の形式に依存しない

### 注意点

1. **メモリ管理**: `malloc` で確保したメモリは必ず `free` する
2. **エラーハンドリング**: 不正な入力に対して適切にエラーを返す
3. **境界チェック**: `start >= from_line` など、ポインタの範囲外アクセスを防ぐ

### 次のステップ

1. 上記のコードを実装
2. コンパイル・実行してテスト
3. valgrindでメモリリークをチェック
4. Python版と出力を比較
5. CPU時間を計測して結果をドキュメント化

---

**参考資料**:
- [C言語の文字列関数 (strchr, strncpy)](https://manual.freebsd.org/cgi/man.cgi?query=strchr)
- [ctype.h の文字判定関数](https://manual.freebsd.org/cgi/man.cgi?query=isalnum)
- [メモリ管理 (malloc, free)](https://manual.freebsd.org/cgi/man.cgi?query=malloc)
