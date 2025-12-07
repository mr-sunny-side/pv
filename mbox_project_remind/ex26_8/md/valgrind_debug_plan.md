# Valgrind デバッグ練習ガイド

## 目的
ex26_8_6.c のバグを、valgrindの出力を読んで自分で見つける練習

## 実行手順

### ステップ1: デバッグビルドの作成

```bash
cd /home/namae/pv/mbox_project_remind/ex26_8
gcc -g -Wall -o ex26_8_6 ex26_8_6.c
```

**オプション説明:**
- `-g`: デバッグシンボルを含める（valgrindで行番号が表示される）
- `-Wall`: すべての警告を表示（コンパイル時の問題も確認）

### ステップ2: 小さいテストケースの作成

23MBのファイルは大きすぎるので、最初の50行だけを使用:

```bash
head -n 50 $MBOX/google.mbox > test_small.mbox
```

### ステップ3: Valgrind実行

```bash
valgrind --leak-check=full \
         --show-leak-kinds=all \
         --track-origins=yes \
         --log-file=valgrind_output.txt \
         ./ex26_8_6 test_small.mbox
```

**オプション説明:**
- `--leak-check=full`: メモリリークの詳細情報
- `--show-leak-kinds=all`: すべての種類のリークを表示
- `--track-origins=yes`: 未初期化値がどこで作られたか追跡
- `--log-file=valgrind_output.txt`: 出力をテキストファイルに保存

### ステップ4: 出力の確認

```bash
cat valgrind_output.txt
```

または、エディタで開く:
```bash
code valgrind_output.txt  # VSCode
vim valgrind_output.txt   # Vim
```

---

## Valgrind出力の読み方

### 出力の基本構造

```
==12345== エラータイプの説明
==12345==    at 0x番地: 関数名 (ファイル名:行番号)
==12345==    by 0x番地: 呼び出し元関数 (ファイル名:行番号)
==12345==    by 0x番地: さらに上の呼び出し元 (ファイル名:行番号)
```

- `==12345==`: プロセスID
- `at`: エラーが発生した場所
- `by`: その関数を呼び出した場所（スタックトレース）

### 主要なエラータイプ

#### 1. Invalid read/write（不正なメモリアクセス）

```
==12345== Invalid read of size 1
==12345==    at 0x...: 関数名 (ファイル名:47)
```

**意味:**
- 読み込み/書き込みしてはいけないメモリにアクセスした
- 配列の範囲外、解放済みメモリなど

**確認すべき点:**
- 指摘された行番号で何をしているか
- ポインタは有効か
- 配列の範囲は正しいか

#### 2. Conditional jump depends on uninitialised value(s)（未初期化変数）

```
==12345== Conditional jump or move depends on uninitialised value(s)
==12345==    at 0x...: 関数名 (ファイル名:47)
```

**意味:**
- 初期化されていない変数を条件式で使っている

**確認すべき点:**
- その変数はいつ値が代入されるか
- 代入前に使われていないか

#### 3. Memory leak（メモリリーク）

```
==12345== 100 bytes in 1 blocks are definitely lost
==12345==    at 0x...: malloc (vg_replace_malloc.c:...)
==12345==    by 0x...: 関数名 (ファイル名:34)
```

**種類:**
- **definitely lost**: 確実にリーク（ポインタを失った）
- **possibly lost**: 可能性あり（ポインタが怪しい位置）
- **still reachable**: 到達可能だが未解放（プログラム終了時）

**確認すべき点:**
- malloc/callocした場所
- 対応するfreeがあるか
- エラーパスでもfreeしているか

---

## デバッグの進め方

### 1. エラーを分類する

出力ファイルを見て、どんなエラーが出ているか確認:
- Invalid read/writeはいくつ？
- 未初期化変数は？
- メモリリークは？

### 2. 行番号を特定する

valgrindが指摘する行番号をメモ:
- `ex26_8_6.c:47` のように表示される

### 3. コードを読む

その行で何をしているか確認:
```c
// 例: 47行目
while ((c = fgetc(*fp)) != EOF || c != '\n')
```

### 4. 問題を推測する

**考えるべき質問:**
- この条件式はいつtrueになる？いつfalseになる？
- ループは終了する条件は何？
- 変数は正しく初期化されている？
- メモリは正しく解放されている？

### 5. 仮説を立てる

例:
- 「このループ条件がおかしい？」
- 「||を&&にすべき？」
- 「この変数は初期化されていない？」

---

## C言語の復習ポイント

### 論理演算子

```c
// OR (||): どちらか一方がtrueならtrue
if (a != 0 || b != 0)  // aかbのどちらかが0でなければtrue

// AND (&&): 両方がtrueの時だけtrue
if (a != 0 && b != 0)  // aもbも0でない時だけtrue
```

### ループの終了条件

```c
// このループはいつ終わる？
while (条件式)

// 条件式がfalseになったら終了
// trueの間は続く
```

### fgetc()の戻り値

```c
int c = fgetc(fp);
// 成功: 読み込んだ文字（0-255）
// EOF: ファイル終端または エラー（通常-1）
```

---

## よくあるバグパターン

### パターン1: 論理演算子の間違い

```c
// 間違い: どちらか一方の条件を満たせば続く
while (c != EOF || c != '\n')

// 正しい: 両方の条件を満たす間続く
while (c != EOF && c != '\n')
```

**考え方:**
- `c != EOF || c != '\n'` は常にtrue（無限ループ）
  - c が EOF なら、`c != '\n'` がtrue
  - c が '\n' なら、`c != EOF` がtrue

### パターン2: メモリ確保後のコピー忘れ

```c
char *email = malloc(size);
// ここでデータをコピーしないと、未初期化のまま
// strncpy() や memcpy() が必要
```

### パターン3: エラーパスでのfree忘れ

```c
char *p = malloc(100);
if (エラー条件) {
    // free(p); を忘れるとリーク
    return 1;
}
free(p);
```

---

## 次のステップ

1. 上記のコマンドでvalgrindを実行
2. `valgrind_output.txt` を開いて読む
3. エラーが指摘する行番号を確認
4. コードを読んで問題を推測
5. 仮説を立てる
6. 詰まったら質問する

**質問する時は:**
- どのエラーメッセージを見ているか
- 自分はどう解釈したか
- どこが分からないか

を伝えてください。間接的なヒントを出します。
