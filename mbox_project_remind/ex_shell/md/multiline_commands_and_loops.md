# シェルの複数行コマンドとループ

## 複数行コマンドの書き方

### 方法1: バックスラッシュ `\` で継続

行の最後に `\` を付けると、次の行に続けることができます。

```bash
valgrind --leak-check=full \
         --show-leak-kinds=all \
         --track-origins=yes \
         --log-file=valgrind_output.txt \
         ./ex26_8_6 test_small.mbox
```

**ポイント:**
- 各行の最後に `\` を付ける（最終行は不要）
- 次の行にスペースでインデントしても問題ない
- `\` の後に**スペースを入れてはいけない**

### 方法2: パイプやセミコロンで自然に改行

パイプ `|` や `&&`, `||` の後は自動的に継続されます。

```bash
cat file.txt |
  grep "pattern" |
  sort |
  uniq
```

```bash
gcc -o program main.c &&
  ./program &&
  echo "Success"
```

### 方法3: クォート内での改行

文字列の途中で改行できます。

```bash
echo "これは
複数行の
テキストです"
```

### 方法4: ヒアドキュメント

複数行のテキストを標準入力に渡せます。

```bash
cat <<EOF
複数行の
内容を
ここに書く
EOF
```

---

## for ループの書き方

### 1行形式（推奨）

**セミコロン `;` で区切る:**

```bash
for i in {1..4}; do mv ex26_8_${i}_*.c ex26_8_${i}.c; done
```

**構造:**
```bash
for 変数 in リスト; do コマンド; done
```

- `for` と `in` の間: ループ変数
- `in` の後: リスト（スペース区切り）
- `do` と `done` の間: 実行するコマンド
- **`;` (セミコロン) が重要**: `do` の前と `done` の前に必要

### 複数行形式

```bash
for i in {1..4}
do
  mv ex26_8_${i}_*.c ex26_8_${i}.c
done
```

または

```bash
for i in {1..4}; do
  mv ex26_8_${i}_*.c ex26_8_${i}.c
done
```

---

## for ループのよくあるトラブル

### 問題: `for>` プロンプトが続いてしまう

```bash
for i in {1..4}
do
  mv ex26_8_${i}_*.c ex26_8_${i}.c
done
for> ← ここで止まってしまう
```

**原因:**
- `done` のスペルミス
- クォートが閉じていない
- 括弧が閉じていない
- 構文エラー

**解決方法:**

1. **Ctrl+C で中断**
   ```bash
   for> [Ctrl+C]
   ^C
   ```

2. **1行形式で書き直す（推奨）**
   ```bash
   for i in {1..4}; do mv ex26_8_${i}_*.c ex26_8_${i}.c; done
   ```

3. **正しく `done` を入力**
   もし構文が正しければ、`done` だけ打って Enter

---

## ブレース展開の注意点

### 間違い: mvで複数ファイルを複数の異なる場所に移動

```bash
# これはエラーになる
mv ex26_8_{1..4}_*.c ex26_8_{1..4}.c
```

**なぜエラー?**

シェルは各ブレース展開を独立して処理します:

```bash
# 左側（移動元）: 4つのパターン
ex26_8_1_*.c ex26_8_2_*.c ex26_8_3_*.c ex26_8_4_*.c

# 右側（移動先）: 4つのファイル名
ex26_8_1.c ex26_8_2.c ex26_8_3.c ex26_8_4.c

# mvコマンドの解釈:
mv ex26_8_1_*.c ex26_8_2_*.c ex26_8_3_*.c ex26_8_4_*.c ex26_8_1.c ex26_8_2.c ex26_8_3.c ex26_8_4.c
```

`mv` は複数の引数を受け取りますが、**最後の引数がディレクトリでない限り**、複数ファイルを複数の異なる場所に移動できません。

### 正解: ループを使う

```bash
for i in {1..4}; do
  mv ex26_8_${i}_*.c ex26_8_${i}.c
done
```

これで各ファイルを個別にリネームできます:
- `ex26_8_1_read_file.c` → `ex26_8_1.c`
- `ex26_8_2_filter_lines.c` → `ex26_8_2.c`
- `ex26_8_3_dynamic_buffer.c` → `ex26_8_3.c`
- `ex26_8_4_extract_email.c` → `ex26_8_4.c`

---

## for ループの実用例

### 例1: 範囲指定

```bash
# 1から10まで
for i in {1..10}; do echo $i; done

# 0から9まで
for i in {0..9}; do echo $i; done

# ステップ指定（1, 3, 5, 7, 9）
for i in {1..10..2}; do echo $i; done
```

### 例2: ファイル一覧

```bash
# カレントディレクトリの.cファイル
for file in *.c; do
  echo "Processing $file"
  gcc -c $file
done
```

### 例3: 複数コマンド実行

```bash
for i in {1..5}; do
  echo "Round $i"
  sleep 1
  echo "Done"
done
```

### 例4: リストから選択

```bash
for name in alice bob charlie; do
  echo "Hello, $name!"
done
```

---

## セミコロンのルール

1行でforループを書く場合、以下の位置にセミコロンが必要:

```bash
for 変数 in リスト; do コマンド1; コマンド2; done
                  ↑        ↑        ↑
                  必須     任意      必須
```

- **`do` の前**: 必須
- **コマンド間**: 複数コマンドがある場合は必須
- **`done` の前**: 最後のコマンドの後は任意（あってもなくてもよい）

**良い例:**
```bash
for i in {1..3}; do echo $i; done
for i in {1..3}; do echo $i; echo "---"; done
```

**悪い例:**
```bash
for i in {1..3} do echo $i done        # エラー: doの前にセミコロンがない
for i in {1..3}; do echo $i echo "---"; done  # エラー: コマンド間にセミコロンがない
```

---

## まとめ

### 複数行コマンド
- `\` で行を継続（最も汎用的）
- パイプ `|` や `&&` の後は自然に継続

### forループ
- **1行形式**: `for i in リスト; do コマンド; done`
- **複数行形式**: `do` と `done` で囲む
- トラブル時は **Ctrl+C** で中断
- **1行形式が確実で推奨**

### ブレース展開
- `mv` で複数ファイルを一度にリネームはできない
- **forループを使う**

### デバッグ
- `for>` から抜けられない → **Ctrl+C**
- セミコロンの位置を確認
- 1行形式で書き直す
