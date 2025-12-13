# ex26_8_6.c の line_num カウントロジックエラー解説

## 概要
このドキュメントでは、[ex26_8_6.c](../ex26_8_6.c) における行番号カウントの重大なロジックエラーと、`count_line` 関数のポインタ記法について解説します。

## 問題のコード

### メインループ (75-88行目)
```c
while (fgets(buffer, sizeof(buffer), fp) != NULL) {
    count_line(fp);
    line_num++;
    if (strncmp(buffer, SEARCH_PREFIX, PREFIX_LEN) == 0) {
        // ... email extraction logic
    }
}
```

### count_line 関数 (42-51行目)
```c
void count_line(FILE *fp)
{
    char c;
    while ((c = fgetc(fp)) != EOF && c != '\\n')
        ;
}
```

## ロジックエラーの詳細

### エラー1: 行番号カウントの二重処理

#### 問題点
`fgets()` は**既に1行分のデータを読み込んでいる**にも関わらず、その後 `count_line(fp)` を呼び出して、ファイルポインタをさらに進めています。

#### 実際の動作
1. `fgets(buffer, sizeof(buffer), fp)` が実行される
   - バッファサイズ (1024バイト) まで読み込む
   - 改行 `\n` に到達したら、**改行を含めて** buffer に格納し、ファイルポインタは次の行の先頭に移動
   - または、バッファが満杯になったら停止（改行に達していない場合）

2. `count_line(fp)` が実行される
   - 既に次の行の先頭にいるファイルポインタから、さらに改行まで読み進める
   - **つまり、次の行を1行スキップしてしまう**

3. `line_num++` が実行される
   - カウンタはインクリメントされるが、実際には2行分のデータが消費されている

#### 具体例
mboxファイルの内容が以下の場合：

```
From: alice@example.com
Subject: Test 1
From: bob@example.com
Subject: Test 2
From: charlie@example.com
```

実際の動作：
- ループ1回目:
  - `fgets()` → "From: alice@example.com\n" を読む（fpは2行目の先頭へ）
  - `count_line()` → 2行目の "Subject: Test 1\n" を**スキップ**（fpは3行目の先頭へ）
  - `line_num` = 1
  - "alice@example.com" を出力

- ループ2回目:
  - `fgets()` → "From: bob@example.com\n" を読む（fpは4行目の先頭へ）
  - `count_line()` → 4行目の "Subject: Test 2\n" を**スキップ**（fpは5行目の先頭へ）
  - `line_num` = 2
  - "bob@example.com" を出力

- ループ3回目:
  - `fgets()` → "From: charlie@example.com\n" を読む（fpはEOFへ）
  - `count_line()` → EOF検出で何もしない
  - `line_num` = 3
  - "charlie@example.com" を出力

**結果**: 1行おきにデータがスキップされる

### エラー2: バッファサイズを超える行の処理

#### 問題点
`fgets()` がバッファサイズ (1024バイト) を超える行を読み込んだ場合、改行文字に到達せずに停止します。この場合、`count_line()` が残りの部分を読み飛ばします。

#### 実際の動作
長い行（1024バイト超）の場合：
1. `fgets()` → 最初の1023バイト + '\0' を buffer に格納（改行なし）
2. `count_line()` → 残りの部分を改行まで読み飛ばす
3. `line_num` は 1 しかインクリメントされない

これは、設計意図としては正しい可能性がありますが、以下の問題があります：
- buffer には行の一部しか入っていない
- `strncmp(buffer, SEARCH_PREFIX, PREFIX_LEN)` は行頭の "From: " しかチェックしないため、検出自体は動作する
- しかし、`ext_sender_and_copy()` に渡される `buffer` には**メールアドレスの一部しか含まれていない可能性**がある

## 正しい実装方法

### 方法1: count_line() を削除（推奨）
```c
while (fgets(buffer, sizeof(buffer), fp) != NULL) {
    line_num++;  // count_line()を呼ばない
    if (strncmp(buffer, SEARCH_PREFIX, PREFIX_LEN) == 0) {
        if (ext_sender_and_copy(buffer, &email) == 1) {
            fprintf(stderr, "Cannot extract email\n");
            free(email);
            fclose(fp);
            return 1;
        }
        printf("%d: %s\n", line_num, email);
        free(email);
    }
}
```

**理由**: `fgets()` は既に1行分を読み込んでおり、ファイルポインタは次の行の先頭に位置しているため、`count_line()` は不要。

### 方法2: バッファサイズを超える行を正しく処理したい場合
```c
while (fgets(buffer, sizeof(buffer), fp) != NULL) {
    size_t len = strlen(buffer);

    // bufferの最後が改行でない場合、残りを読み飛ばす
    if (len > 0 && buffer[len - 1] != '\n') {
        char c;
        while ((c = fgetc(fp)) != EOF && c != '\n')
            ;
    }

    line_num++;

    if (strncmp(buffer, SEARCH_PREFIX, PREFIX_LEN) == 0) {
        // ... email extraction logic
    }
}
```

**理由**: 改行が buffer に含まれていない場合のみ、残りを読み飛ばす。

## count_line 関数のポインタ記法について

### 質問: `FILE *fp` vs `FILE **fp`

#### 答え: `FILE *fp` (単一のアスタリスク) が正しい

#### 理由

1. **関数が FILE ポインタ自体を変更しない**
   - `count_line()` は `fp` が指す `FILE` 構造体の**内部状態**（ファイル位置など）を変更する
   - しかし、`fp` **ポインタ変数自体**の値（アドレス）は変更しない

2. **C言語のポインタ渡しの仕組み**
   ```c
   void count_line(FILE *fp)
   {
       // fpはFILEポインタのコピー
       // fgetc(fp)はfpが指すFILE構造体を変更するが、
       // fpポインタ自体（アドレス値）は変更しない
       char c;
       while ((c = fgetc(fp)) != EOF && c != '\\n')
           ;
   }

   // main関数から呼び出し
   FILE *fp = fopen("file.txt", "r");
   count_line(fp);  // fpのコピーが渡される
   // fpは同じアドレスを指しているが、FILE構造体の内部状態は変化している
   ```

3. **`FILE **fp` が必要なケース**
   - ポインタ変数自体を変更したい場合（例: `fopen` の結果を受け取りたい場合）
   ```c
   int open_file(const char *filename, FILE **fp)
   {
       *fp = fopen(filename, "r");  // ポインタ自体を変更
       if (*fp == NULL)
           return 1;
       return 0;
   }

   // 使用例
   FILE *fp;
   if (open_file("data.txt", &fp) != 0) {
       fprintf(stderr, "Error opening file\n");
       return 1;
   }
   ```

4. **実際の動作比較**
   ```c
   // FILE *fp の場合（正しい）
   void count_line(FILE *fp)
   {
       fgetc(fp);  // OK: fpが指すFILE構造体を操作
   }

   // FILE **fp の場合（不正）
   void count_line(FILE **fp)
   {
       fgetc(*fp);  // 動作はするが、不必要な間接参照
       // 呼び出し側: count_line(&fp); と呼ぶ必要がある
   }
   ```

### 結論
- **`FILE *fp` が正しい**: `count_line()` は FILE ポインタの値を変更しないため
- **`FILE **fp` は不要**: ポインタ自体を書き換える必要がない場合は使わない
- あなたの直感で `**` に変えたのは誤りで、元の `*` が正しい実装です

## まとめ

### 主な問題点
1. `count_line(fp)` の呼び出しにより、1行おきにデータがスキップされる
2. `line_num` のカウントが実際に処理された行と一致しない
3. 長い行の処理において、メールアドレスが途中で切れる可能性がある

### 推奨修正
- **`count_line(fp)` の呼び出しを削除**する（76行目）
- `fgets()` は既に改行まで読み込むか、バッファ満杯まで読み込むため、追加の行カウント処理は不要

### ポインタ記法
- `void count_line(FILE *fp)` が正しい
- `FILE **fp` に変更する必要はない

## 参考: fgets() の動作仕様

```c
char *fgets(char *s, int size, FILE *stream);
```

- 最大 `size - 1` 文字を読み込む
- 改行文字 `\n` に到達したら、**改行を含めて** 文字列に格納し、停止
- 改行の後に `\0` を追加
- ファイルポインタは改行の次の文字（次の行の先頭）に移動
- バッファが満杯になった場合は、改行に達していなくても停止
