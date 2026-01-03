# Shell Script 学習ドキュメント - 独立した実行可能スクリプトの作り方

**日付**: 2024-12-10
**対象**: ex26_8_6.sh
**目的**: 設定ファイル（zshrc）を汚さず、実行時だけ動く独立したスクリプトの書き方を学ぶ

---

## 目次

1. [実行可能スクリプトの基本構造](#実行可能スクリプトの基本構造)
2. [shebang行の説明](#shebang行の説明)
3. [関数定義と実行制御](#関数定義と実行制御)
4. [環境変数の設定](#環境変数の設定)
5. [引数チェックとエラーハンドリング](#引数チェックとエラーハンドリング)
6. [完全な実装例](#完全な実装例)
7. [実行方法](#実行方法)

---

## 実行可能スクリプトの基本構造

Shell Scriptには大きく2つの使い方があります：

### パターン1: 関数定義のみ（source用）

```bash
# zshrcなどから読み込む用
ex26_8_ex() {
    echo "This is a function"
}
```

**使い方**:
```bash
source ex26_8_6.sh
ex26_8_ex
```

**メリット**:
- シェル環境に関数を追加できる
- 一度読み込めば何度でも使える

**デメリット**:
- 設定ファイルを汚す
- シェル環境に依存する

---

### パターン2: 独立した実行可能スクリプト（推奨）

```bash
#!/bin/bash

# 環境変数の設定
export VARIABLE="value"

# 関数定義
my_function() {
    echo "This is a function"
}

# 実行制御
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    my_function
fi
```

**使い方**:
```bash
chmod +x script.sh
./script.sh
```

**メリット**:
- 設定ファイルを汚さない
- 独立して動作する
- 他の環境でも動く

**デメリット**:
- 実行のたびにファイルを指定する必要がある

---

## shebang行の説明

### shebangとは

スクリプトファイルの**1行目**に書く特殊なコメント行です。

```bash
#!/bin/bash
```

### 役割

- このスクリプトをどのインタプリタで実行するかを指定
- `./script.sh` で実行したとき、自動的に `/bin/bash script.sh` が実行される

### よく使うshebang

| shebang | 説明 |
|---------|------|
| `#!/bin/bash` | Bash で実行 |
| `#!/bin/zsh` | Zsh で実行 |
| `#!/bin/sh` | POSIX シェルで実行（移植性が高い） |
| `#!/usr/bin/env bash` | `bash` のパスを自動検出（推奨） |
| `#!/usr/bin/env python3` | Python 3 で実行 |

### なぜ `/usr/bin/env` を使うのか

```bash
#!/usr/bin/env bash
```

**理由**:
- `bash` がどこにインストールされていても動作する
- macOS では `/bin/bash`、一部のLinuxでは `/usr/bin/bash` など、環境で異なる場合がある
- `env` コマンドが `PATH` から `bash` を探してくれる

---

## 関数定義と実行制御

### 問題: 関数定義だけでは実行されない

```bash
#!/bin/bash

ex26_8_ex() {
    echo "Hello"
}
```

このスクリプトを実行しても、関数が定義されるだけで**何も出力されません**。

---

### 解決策1: 関数を直接呼び出す

```bash
#!/bin/bash

ex26_8_ex() {
    echo "Hello"
}

# 関数を呼び出す
ex26_8_ex
```

**問題点**:
- このスクリプトを `source` で読み込むと、勝手に実行されてしまう
- 関数定義のみを読み込みたい場合に不便

---

### 解決策2: 実行制御を使う（推奨）

```bash
#!/bin/bash

ex26_8_ex() {
    echo "Hello"
}

# スクリプトとして実行された場合のみ関数を呼び出す
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    ex26_8_ex
fi
```

### `${BASH_SOURCE[0]}` と `${0}` の違い

| 変数 | 意味 |
|------|------|
| `${BASH_SOURCE[0]}` | スクリプトファイルのパス（source されても変わらない） |
| `${0}` | 実行中のシェルまたはスクリプトの名前 |

### 動作

| 実行方法 | `${BASH_SOURCE[0]}` | `${0}` | 一致する？ |
|---------|---------------------|--------|----------|
| `./script.sh` | `./script.sh` | `./script.sh` | ✓ はい → 実行される |
| `source script.sh` | `script.sh` | `bash` | ✗ いいえ → 実行されない |

---

### Python の `if __name__ == '__main__'` との比較

Pythonにも同じ仕組みがあります：

**Python**:
```python
def my_function():
    print("Hello")

if __name__ == '__main__':
    my_function()
```

**Bash**:
```bash
my_function() {
    echo "Hello"
}

if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    my_function
fi
```

どちらも「スクリプトとして実行された場合のみ処理を実行する」という同じ目的です。

---

## 環境変数の設定

### 問題: zshrcに依存すると他の環境で動かない

```bash
#!/bin/bash

# $MBOX_PROJECT は zshrc で定義されている前提
ex26_8_ex() {
    echo $MBOX_PROJECT  # zshrcがないと空になる
}
```

### 解決策: スクリプト内で環境変数を定義

```bash
#!/bin/bash

# 環境変数の設定
export MBOX_PROJECT="$HOME/pv/mbox_project_remind"
export C_FILE="$MBOX_PROJECT/test_case/out"
export MBOX="$MBOX_PROJECT/mbox"

ex26_8_ex() {
    echo $MBOX_PROJECT  # 常に動作する
}
```

### `export` の役割

| 書き方 | スコープ | 説明 |
|--------|---------|------|
| `VAR="value"` | ローカル変数 | このスクリプト内でのみ有効 |
| `export VAR="value"` | 環境変数 | 子プロセスにも引き継がれる |

**例**:
```bash
#!/bin/bash

VAR1="local"
export VAR2="exported"

# 子プロセスを起動
bash -c 'echo $VAR1'  # 出力: （空）
bash -c 'echo $VAR2'  # 出力: exported
```

---

## 引数チェックとエラーハンドリング

### 基本的な引数チェック

```bash
if [ $# -ne 1 ]; then
    echo "Argument Error"
    echo "Usage: $0 [program name]"
    exit 1
fi
```

### 特殊変数の説明

| 変数 | 意味 |
|------|------|
| `$#` | 引数の個数 |
| `$0` | スクリプト名 |
| `$1`, `$2`, ... | 第1引数、第2引数、... |
| `$@` | すべての引数（配列） |
| `$?` | 直前のコマンドの終了ステータス |

### 引数の検証例

```bash
#!/bin/bash

# 引数が1つでない場合はエラー
if [ $# -ne 1 ]; then
    echo "Argument Error" >&2
    echo "Usage: $0 [program name]" >&2
    exit 1
fi

# ファイルの存在チェック
prog_file="$1"
if [ ! -f "$prog_file" ]; then
    echo "Error: File not found: $prog_file" >&2
    exit 1
fi

echo "Processing $prog_file..."
```

### エラー出力のリダイレクト

```bash
echo "Error message" >&2
```

- `>&2`: 標準エラー出力（stderr）にリダイレクト
- エラーメッセージは stderr に出力するのが慣例

### 終了ステータス

| 値 | 意味 |
|----|------|
| `0` | 成功 |
| `1` | 一般的なエラー |
| `2` | 使用方法のエラー |
| `127` | コマンドが見つからない |

---

## 完全な実装例

### ex26_8_6.sh の完全版

```bash
#!/bin/bash

# ==========================================
# C言語版とPython版のCPU時間比較スクリプト
# ==========================================

# 環境変数の設定
export MBOX_PROJECT="$HOME/pv/mbox_project_remind"
export C_FILE="$MBOX_PROJECT/test_case/out"
export MBOX="$MBOX_PROJECT/mbox"

# 比較関数
ex26_8_ex() {
    local prog=$1
    local prog_c=$C_FILE/${prog}_file
    local prog_py=$MBOX_PROJECT/ex26_8/${prog}.py
    local mbox=$MBOX/google.mbox
    local output=$MBOX_PROJECT/ex26_8/txt/${prog}_sh.txt

    # ファイルの存在チェック
    if [ ! -f "$prog_c" ]; then
        echo "Error: C executable not found: $prog_c" >&2
        return 1
    fi

    if [ ! -f "$prog_py" ]; then
        echo "Error: Python file not found: $prog_py" >&2
        return 1
    fi

    if [ ! -f "$mbox" ]; then
        echo "Error: mbox file not found: $mbox" >&2
        return 1
    fi

    # 結果ファイルの初期化
    echo "========== C result ==========" > "$output"
    echo "" >> "$output"

    # C言語版を5回実行
    echo "Running C version (5 iterations)..."
    for i in {1..5}; do
        ("$prog_c" "$mbox" 2>&1) | grep "Processing Time" >> "$output"
    done

    echo "========== Python result ==========" >> "$output"
    echo "" >> "$output"

    # Python版を5回実行
    echo "Running Python version (5 iterations)..."
    for i in {1..5}; do
        (python3 "$prog_py" "$mbox" 2>&1) | grep "Processing Time" >> "$output"
    done

    # 結果の表示
    echo ""
    echo "=========================================="
    echo "Comparison completed!"
    echo "Results saved to: $output"
    echo "=========================================="
    echo ""
    cat "$output"
}

# スクリプトとして実行された場合のみ関数を呼び出す
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    # 引数チェック
    if [ $# -ne 1 ]; then
        echo "Argument Error" >&2
        echo "Usage: $0 [program name without extension]" >&2
        echo "Example: $0 ex26_8_6" >&2
        exit 1
    fi

    # 関数を実行
    ex26_8_ex "$1"
fi
```

---

## コードの詳細解説

### 1. ローカル変数の使用

```bash
ex26_8_ex() {
    local prog=$1  # 関数内でのみ有効な変数
    local prog_c=$C_FILE/${prog}_file
    # ...
}
```

**なぜ `local` を使うのか**:
- グローバル変数との衝突を避ける
- 関数を終了すると変数が破棄される
- 意図しない副作用を防ぐ

### 2. パス展開とクォート

```bash
# 悪い例（スペースを含むパスで失敗）
if [ ! -f $prog_c ]; then

# 良い例（必ずクォートする）
if [ ! -f "$prog_c" ]; then
```

### 3. サブシェルとパイプ

```bash
("$prog_c" "$mbox" 2>&1) | grep "Processing Time" >> "$output"
```

- `( ... )`: サブシェルで実行（現在のシェルに影響を与えない）
- `2>&1`: 標準エラー出力を標準出力にリダイレクト
- `| grep`: パイプでフィルタリング
- `>> "$output"`: 追記モードでファイルに出力

### 4. ループ構文

```bash
for i in {1..5}; do
    # 処理
done
```

- `{1..5}`: 1から5までの数列を生成
- `$i` でループカウンタにアクセス（今回は未使用）

---

## 実行方法

### 1. 実行権限の付与（初回のみ）

```bash
chmod +x ex26_8/ex26_8_6.sh
```

### 2. スクリプトの実行

```bash
cd /home/namae/pv/mbox_project_remind/ex26_8
./ex26_8_6.sh ex26_8_6
```

または、フルパスで実行：

```bash
/home/namae/pv/mbox_project_remind/ex26_8/ex26_8_6.sh ex26_8_6
```

### 3. 出力の確認

```bash
cat ex26_8/txt/ex26_8_6_sh.txt
```

---

## 使用例

### 正常実行

```bash
$ ./ex26_8_6.sh ex26_8_6
Running C version (5 iterations)...
Running Python version (5 iterations)...

==========================================
Comparison completed!
Results saved to: /home/namae/pv/mbox_project_remind/ex26_8/txt/ex26_8_6_sh.txt
==========================================

========== C result ==========

Processing Time: 0.123 s
Processing Time: 0.125 s
Processing Time: 0.122 s
Processing Time: 0.124 s
Processing Time: 0.123 s
========== Python result ==========

Processing Time: 0.456 s
Processing Time: 0.458 s
Processing Time: 0.455 s
Processing Time: 0.457 s
Processing Time: 0.456 s
```

### エラーケース1: 引数なし

```bash
$ ./ex26_8_6.sh
Argument Error
Usage: ./ex26_8_6.sh [program name without extension]
Example: ./ex26_8_6.sh ex26_8_6
```

### エラーケース2: 存在しないプログラム

```bash
$ ./ex26_8_6.sh nonexistent
Error: C executable not found: /home/namae/pv/mbox_project_remind/test_case/out/nonexistent_file
```

---

## source で読み込む場合

このスクリプトは `source` でも読み込めます：

```bash
source ex26_8/ex26_8_6.sh

# 関数が定義される（実行はされない）
ex26_8_ex ex26_8_6
```

この場合：
- `${BASH_SOURCE[0]}` ≠ `${0}` なので、自動実行されない
- 関数のみがシェル環境に追加される

---

## まとめ

### 独立した実行可能スクリプトの要件

1. **shebang行**: `#!/bin/bash` または `#!/usr/bin/env bash`
2. **環境変数の設定**: 外部依存を避ける
3. **実行制御**: `if [ "${BASH_SOURCE[0]}" = "${0}" ]` で制御
4. **引数チェック**: `if [ $# -ne 1 ]` などで検証
5. **エラーハンドリング**: 終了ステータスとエラー出力
6. **実行権限**: `chmod +x script.sh`

### 設定ファイル（zshrc）を汚さないメリット

- **ポータビリティ**: 他の環境でも動く
- **独立性**: シェル環境に依存しない
- **保守性**: スクリプトを削除すれば完全に消える
- **明確性**: 何をしているかが明確

### Pythonとの比較

| 項目 | Python | Bash |
|------|--------|------|
| 実行制御 | `if __name__ == '__main__'` | `if [ "${BASH_SOURCE[0]}" = "${0}" ]` |
| shebang | `#!/usr/bin/env python3` | `#!/usr/bin/env bash` |
| 引数 | `sys.argv` | `$1`, `$2`, ... |
| 終了 | `sys.exit(1)` | `exit 1` |

---

## 参考資料

- [Bash リファレンスマニュアル](https://www.gnu.org/software/bash/manual/)
- [Advanced Bash-Scripting Guide](https://tldp.org/LDP/abs/html/)
- [ShellCheck](https://www.shellcheck.net/) - Shell Script の静的解析ツール

---

## 次のステップ

1. 実際にスクリプトを書いて実行する
2. ShellCheck で静的解析してみる
3. より複雑なスクリプト（複数のサブコマンドなど）に挑戦する
4. エラーハンドリングを強化する（trap コマンドなど）
