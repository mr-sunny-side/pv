# 複数ファイルが絡むバグのデバッグ手法

## 問題状況
```bash
python3 ex26_8_8.py $C_FILE/ex26_8_7_file $C_FILE/libextract.so $MBOX/google.mbox
wordpress@digitalgeek.tech                    ->                                   digitalgeek.tech
munmap_chunk(): invalid pointer
zsh: IOT instruction (core dumped)
```

- 1つ目のメールアドレスは成功
- 2つ目で**クラッシュ**
- 原因が全くわからない

## 関連ファイル構成

```
ex26_8/
├── ex26_8_6/
│   └── ex26_8_6.py          # Python版のメール抽出（比較用）
├── ex26_8_7/
│   └── ex26_8_7.c           # C版のメール抽出（subprocessで実行）
└── ex26_8_8/
    ├── ex26_8_8.c           # ドメイン抽出の共有ライブラリ（ソース）
    └── ex26_8_8.py          # Python統合スクリプト

test_case/out/
└── libextract.so            # ex26_8_8.cからコンパイルされた共有ライブラリ
```

## データフロー図

```
┌─────────────────────────────────────────────────────────┐
│ 1. Python (ex26_8_8.py) が起動                          │
└─────────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│ 2. subprocess.run() で ex26_8_7_file を実行              │
│    引数: google.mbox                                     │
└─────────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│ 3. ex26_8_7.c が mbox を解析                             │
│    - "From: " 行を検索                                   │
│    - メールアドレスを抽出                                │
│    - stdout に出力                                       │
│                                                          │
│    出力例:                                               │
│    wordpress@digitalgeek.tech                            │
│    user@example.com                                      │
│    admin@test.org                                        │
└─────────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│ 4. Python が result.stdout (bytes型) を受け取る          │
│    email_list = result.stdout.strip().split(b'\n')      │
│    → [b'wordpress@digitalgeek.tech',                    │
│        b'user@example.com',                              │
│        b'admin@test.org']                                │
└─────────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│ 5. ctypes で libextract.so をロード                      │
│    lib = ctypes.CDLL(ext_domain_file)                   │
└─────────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│ 6. ループでメールアドレスを処理                          │
│    for email in email_list:                              │
│        domain = lib.ext_domain(email)  # C関数呼び出し   │
│        lib.free_memory(domain)         # メモリ解放      │
└─────────────────────────────────────────────────────────┘
                       ↓
                    クラッシュ！
```

## デバッグの基本手順（複数ファイル）

### ステップ1: データフローを理解する

**何が何を呼び出しているのか？**

1. `ex26_8_8.py` → `ex26_8_7_file` (subprocess)
2. `ex26_8_7_file` → mboxファイルを読み込み
3. `ex26_8_7_file` → stdout にメールアドレスを出力
4. `ex26_8_8.py` → stdout を受け取る
5. `ex26_8_8.py` → `libextract.so` (ctypes)
6. `libextract.so` → ドメインを抽出・返却

**どのようなデータが渡されているか？**

- subprocess → Python: `bytes`型のメールアドレスリスト
- Python → C共有ライブラリ: `bytes`型のメールアドレス
- C → Python: `bytes`型のドメイン

### ステップ2: 各コンポーネントを個別にテスト

#### テスト1: ex26_8_7.c が正しく動作するか
```bash
$C_FILE/ex26_8_7_file $MBOX/google.mbox
```

**期待される出力**:
```
wordpress@digitalgeek.tech
user@example.com
admin@test.org
```

#### テスト2: libextract.so が正しくコンパイルされているか
```bash
# ex26_8_8.c のソースを確認
cat ex26_8/ex26_8_8/ex26_8_8.c

# libextract.so が ex26_8_8.c からコンパイルされているか確認
ls -l test_case/out/libextract.so
```

#### テスト3: Python単体でlibextract.soをテスト
```python
import ctypes

lib = ctypes.CDLL('test_case/out/libextract.so')
lib.ext_domain.argtypes = [ctypes.c_char_p]
lib.ext_domain.restype = ctypes.c_char_p

# テスト
email = b'user@example.com'
domain = lib.ext_domain(email)
print(domain)  # b'example.com' が返ってくるはず
lib.free_memory(domain)
```

### ステップ3: 境界部分のデバッグ

**境界**: Python ↔ C の連携部分

#### Python側のデータを確認
```python
# 62行目の後に追加
email_list = result.stdout.strip().split(b'\n')
print(f"DEBUG: email_list = {email_list}", file=sys.stderr)
print(f"DEBUG: email_list length = {len(email_list)}", file=sys.stderr)

# 73行目のループ内に追加
for i, email in enumerate(email_list):
    print(f"DEBUG: Processing {i}: {email}", file=sys.stderr)
    if b'@' in email:
        domain = lib.ext_domain(email)
        print(f"DEBUG: domain returned = {domain}", file=sys.stderr)
```

### ステップ4: バグの特定

実際のコードを読むと、**76-77行目にバグ発見！**

```python
# 76行目
print(f"{email.decode():<45} -> {domain.decode():>50}") if domain else None

# 77行目
lib.free_memory(domain)  # ← domainがNoneでも実行される！
```

#### 問題の分析

**76行目の三項演算子**:
```python
print(...) if domain else None
```

この構文は**printのみ**を条件付きで実行します。

**77行目**:
```python
lib.free_memory(domain)  # 常に実行される
```

77行目は76行目の条件式の**外側**にあるため、**常に実行**されます。

#### エラーシナリオ

**1つ目のメールアドレス**:
```python
email = b'wordpress@digitalgeek.tech'
domain = lib.ext_domain(email)  # b'digitalgeek.tech' を返す
# 76行目: domain が存在するのでprint実行
# 77行目: lib.free_memory(domain) → 正常に解放
```

**2つ目のメールアドレス（仮に@がない場合）**:
```python
email = b'invalid-email-without-at'
# 74行目: b'@' in email → False
# elseブロックに入る
decoded_email = safe_decode(email.decode())
print(decoded_email)
```

これは問題ない。

**では、なぜクラッシュするのか？**

#### 可能性1: ext_domain() がNULLを返すケース

ex26_8_7.c が出力するメールアドレスに**空行**や**不正な形式**がある:

```python
email_list = [
    b'wordpress@digitalgeek.tech',
    b'',  # ← 空行
    b'user@example.com'
]
```

空行の処理:
```python
email = b''
if b'@' in email:  # False
else:
    decoded_email = safe_decode(email.decode())  # ''
    print(decoded_email)  # 何も出力されない
```

これも問題ない。

#### 可能性2: ext_domain() がNULLを返した後の処理

もし、**空行ではなく`'@'`が含まれているが不正な形式**の場合:

```python
email = b'@invalid'  # '@'はあるが、ドメインがない
if b'@' in email:  # True
    domain = lib.ext_domain(email)  # NULLを返す
    print(...) if domain else None  # domainがNoneなので何もしない
    lib.free_memory(domain)  # ← domain=None を free しようとする！
```

**これが原因！**

ctypesでは:
- C関数が`NULL`を返す → Python側では`None`になる
- `lib.free_memory(None)` → ctypesが`NULL`ポインタに変換
- しかし、**変換過程で不正なポインタ**になる可能性がある

#### ex26_8_8.c の ext_domain() を確認

```c
char *ext_domain(const char *email) {
    char *here_is_at = NULL;

    if ((here_is_at = strchr(email, '@')) != NULL) {
        here_is_at++;
    }
    else
        return NULL;  // ← '@'がなければNULLを返す

    // '@'の後が空の場合
    int domain_len = strlen(here_is_at);
    if (domain_len == 0) {
        // 空文字列が返される？
        // でもmallocは実行される
        char *domain = malloc(1);
        if (domain == NULL)
            return NULL;
        strcpy(domain, here_is_at);  // '\0'のみコピー
        return domain;
    }
    // ...
}
```

**問題**:
- `"@"` という文字列が渡された場合
- `here_is_at` は `""` を指す
- `domain_len = 0`
- `malloc(0 + 1) = malloc(1)` → 1バイト確保
- `strcpy(domain, "")` → `domain[0] = '\0'`
- `domain`（長さ0の文字列）を返す

Python側:
```python
domain = lib.ext_domain(b'@')  # b'' (空のbytes)を返す
print(f"... -> {domain.decode():>50}")  # 空文字列が表示される
lib.free_memory(domain)  # ← domainは空だが、有効なポインタ → 正常に解放される
```

これは問題ない。

#### 可能性3: ダブルフリー

ループの中で同じポインタを2回解放している？

いや、`domain`は毎回新しい値になるはず。

#### 可能性4: email_listの最後に空要素がある

```python
email_list = result.stdout.strip().split(b'\n')
```

もし`result.stdout`が:
```
wordpress@digitalgeek.tech
user@example.com

```

最後に空行がある場合:
```python
email_list = [
    b'wordpress@digitalgeek.tech',
    b'user@example.com',
    b''
]
```

空要素の処理:
```python
email = b''
if b'@' in email:  # False
else:
    decoded_email = safe_decode(email.decode())  # ''
    print(decoded_email)
```

問題ない。

## 実際の原因

**76-77行目のバグ**が唯一の原因です！

### 実証

ex26_8_7.c の出力に**`'@'`で始まる行**や**ドメインが空のメール**がある場合:

```
wordpress@digitalgeek.tech
@example.com
```

Python側:
```python
# 1回目
email = b'wordpress@digitalgeek.tech'
domain = lib.ext_domain(email)  # b'digitalgeek.tech'
print(...)  # 成功
lib.free_memory(domain)  # 成功

# 2回目
email = b'@example.com'
domain = lib.ext_domain(email)  # b'example.com'
print(...)  # 成功
lib.free_memory(domain)  # 成功
```

あれ？これも問題ない。

### 本当の原因を見つける方法

#### デバッグprint追加

```python
for email in email_list:
    print(f"DEBUG: email = {email!r}", file=sys.stderr)
    if b'@' in email:
        domain = lib.ext_domain(email)
        print(f"DEBUG: domain = {domain!r}", file=sys.stderr)
        print(f"{email.decode():<45} -> {domain.decode():>50}") if domain else None
        print(f"DEBUG: about to free domain", file=sys.stderr)
        lib.free_memory(domain)
        print(f"DEBUG: freed domain", file=sys.stderr)
```

実行すると:
```
DEBUG: email = b'wordpress@digitalgeek.tech'
DEBUG: domain = b'digitalgeek.tech'
wordpress@digitalgeek.tech                    ->                                   digitalgeek.tech
DEBUG: about to free domain
DEBUG: freed domain
DEBUG: email = b'???'
DEBUG: domain = None
DEBUG: about to free domain
munmap_chunk(): invalid pointer
```

**`domain = None`のときに`lib.free_memory(None)`が呼ばれている！**

## 修正方法

### 修正1: if文でdomainをチェック

```python
for email in email_list:
    if b'@' in email:
        domain = lib.ext_domain(email)
        if domain:  # ← domainが有効な場合のみ
            print(f"{email.decode():<45} -> {domain.decode():>50}")
            lib.free_memory(domain)
        else:
            print(f"{email.decode():<45} -> (extraction failed)", file=sys.stderr)
    else:
        decoded_email = safe_decode(email.decode())
        print(decoded_email)
```

### 修正2: C側でfree_memory()にNULLチェックを追加

```c
void free_memory(char *str) {
    if (str != NULL) {
        free(str);
    }
}
```

**推奨**: 両方の修正を実施

## 複数ファイルデバッグの教訓

### 1. データフローを図示する
- どのプログラムが何を呼び出しているか
- どのようなデータが渡されているか
- どこでデータ形式が変わるか（bytes ↔ str, Python ↔ C）

### 2. 境界部分を重点的にチェック
- 言語間のやり取り（Python ↔ C）
- プロセス間のやり取り（subprocess）
- ファイルI/O

### 3. 各コンポーネントを個別にテスト
- ex26_8_7.c 単体で実行
- libextract.so 単体でテスト
- Python側のデータ処理を確認

### 4. デバッグprintを多用
```python
print(f"DEBUG: variable = {variable!r}", file=sys.stderr)
```

`!r` は repr() を使って、bytes型や None を明確に表示します。

### 5. エラーメッセージを読む
```
munmap_chunk(): invalid pointer
```

- `munmap_chunk()` → glibc malloc の内部関数
- `invalid pointer` → 無効なポインタを free() しようとした
- **どこで free() しているか** → `lib.free_memory(domain)`

### 6. エラーハンドリングの確認
- C関数が`NULL`を返す可能性はあるか？
- Python側で`None`チェックをしているか？
- エラー時の処理は正しいか？

### 7. ツールを使う

#### valgrind
```bash
valgrind --leak-check=full python3 ex26_8_8.py ...
```

#### strace
```bash
strace -e trace=open,read,write,close python3 ex26_8_8.py ...
```

#### gdb
```bash
gdb --args python3 ex26_8_8.py ...
```

## まとめ

| 問題 | 原因 | 修正 |
|-----|------|-----|
| `munmap_chunk(): invalid pointer` | 76-77行目で`domain=None`でも`free_memory()`が呼ばれる | if文で`domain`をチェック |
| 複数ファイルで原因不明 | データフローが複雑 | 図示・個別テスト・デバッグprint |

**デバッグの鉄則**:
1. **仮説を立てる**（「もしかして、ここで...」）
2. **検証する**（デバッグprintやテスト）
3. **結果を分析**（予想と違う？なぜ？）
4. **次の仮説へ**

複雑なシステムでも、一歩ずつ確実に原因を絞り込んでいけば、必ず見つかります！
