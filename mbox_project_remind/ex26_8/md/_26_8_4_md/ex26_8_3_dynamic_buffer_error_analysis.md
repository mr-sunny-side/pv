# エラー解説: ex26_8_3_dynamic_buffer.c

## プログラムの意図
"From: "で始まる行を動的メモリに保存し、最後にまとめて表示するプログラム。

## 🔴 致命的なエラー

### エラー1: 未初期化変数の使用（59-64行目）
```c
int	malloc_result;
while (...) {
    if (strncmp(buffer, SEARCH_PREFIX, PREFIX_LEN) == 0) {
        malloc_result = line_malloc(line, buffer, line_num);
    }
    if (malloc_result == 1) {  // ← 未初期化の可能性
        free_err_line(line, line_num);
        return 1;
    }
```

**問題点**:
- `malloc_result`が初期化されていない
- `strncmp`が一致しない行では、`malloc_result`は未定義値
- 61行目の判定が予測不能な動作をする（未定義動作）

**実際に起きること**:
```
1行目: "Hello"          → strncmp不一致 → malloc_result未初期化（例: ゴミ値123）
2行目: 判定時          → if (123 == 1) → false（運が良ければ）
3行目: "From: Alice"   → malloc_result = 0（成功）
4行目: 判定時          → if (0 == 1) → false
5行目: "Bye"           → strncmp不一致 → malloc_result = 0（前の値が残る）
```

**修正方法**:
```c
int	malloc_result = 0;  // 初期化必須
```

---

### エラー2: インデックスのミスマッチ（致命的なバグ）

#### 問題2-1: malloc済み配列への不正アクセス（65行目）
```c
while (...) {
    if (strncmp(buffer, SEARCH_PREFIX, PREFIX_LEN) == 0) {
        malloc_result = line_malloc(line, buffer, line_num);  // line[line_num]をmalloc
    }
    // ...
    strcpy(line[line_num], buffer);  // ← 常に実行される！
```

**問題点**:
- `malloc`は`strncmp`が一致した時だけ実行
- しかし`strcpy`は**毎回**実行される
- `strncmp`が不一致の行では、`line[line_num]`は未初期化ポインタ

**実際に起きること**:
```
1行目: "Hello"
  → malloc実行されない
  → line[1]は未初期化（NULL or ゴミポインタ）
  → strcpy(line[1], buffer) ← セグメンテーションフォルト！
```

#### 問題2-2: line_numのカウント方法の矛盾
```c
int	line_num = 1;  // ファイルの行番号として使用

// main関数内
line[line_num]  // 配列インデックスとして使用（0始まりでない）

// 最後のループ
for (i = 0; i < line_num; i++)  // 0から開始
```

**問題点**:
- `line_num = 1`から開始
- `line[1]`, `line[2]`, ...にアクセス
- しかし最後のループは`line[0]`から開始
- `line[0]`は一度も初期化されない（未定義動作）
- 実際に使った`line[1], line[2], ...`は解放されない（メモリリーク）

**配列の実態**:
```
期待:
line[0] = "From: Alice\n"
line[1] = "From: Bob\n"
line[2] = NULL

実際:
line[0] = 未初期化（ゴミポインタ）
line[1] = "From: Alice\n"
line[2] = "From: Bob\n"
↓
for (i = 0; i < 3; i++)
  printf("%s", line[i]);  // line[0]がゴミでクラッシュ
  free(line[i]);
```

---

### エラー3: move_fp関数のロジックエラー（28-37行目）
```c
void	move_fp(FILE *fp)
{
	int	c;
	while ((c = fgetc(fp)) != EOF && c != '\n') {
		;
		if (c == '\n')  // ← この行は絶対に実行されない
			break;
	}
	printf("End of File\n");  // ← 誤解を招く
}
```

**問題点**:
1. while条件で`c != '\n'`をチェック済み
2. ループ内の`if (c == '\n')`は常にfalse（到達不能コード）
3. `printf("End of File\n")`は毎回表示される（EOFの時だけではない）

**修正方法**:
```c
void	move_fp(FILE *fp)
{
	int	c;
	while ((c = fgetc(fp)) != EOF && c != '\n')
		;
	// 改行またはEOFまで読み飛ばすだけ（printfは不要）
}
```

---

### エラー4: line_malloc関数の設計ミス（10-19行目）
```c
int	line_malloc(char **line, char *buffer, int line_num)
{
	line[line_num] = malloc(strlen(buffer) + 1);
	if (line[line_num] == NULL) {
		fprintf(stderr, "Memory allocation failed\n");
		return 1;
	}
	return 0;
}
```

**問題点**:
- `malloc`するだけで、`buffer`の内容をコピーしていない
- 呼び出し側で別途`strcpy`が必要
- 関数名が誤解を招く（`line_malloc`だがデータコピーしない）

**改善案**:
```c
int	line_malloc_and_copy(char **line, const char *buffer, int line_num)
{
	line[line_num] = malloc(strlen(buffer) + 1);
	if (line[line_num] == NULL) {
		fprintf(stderr, "Memory allocation failed\n");
		return 1;
	}
	strcpy(line[line_num], buffer);  // ここでコピー
	return 0;
}
```

---

### エラー5: 出力カウントの誤り（77行目）
```c
printf("=== Found %d matching line ===\n", line_num);
```

**問題点**:
- `line_num`は最終的に「次の行番号」を指す
- 実際の一致行数ではない

**例**:
```
ファイル内容:
1: Hello
2: From: Alice  ← 一致
3: World
4: From: Bob    ← 一致

line_numの変遷:
初期値: 1
1行目処理後: 2
2行目処理後: 3
3行目処理後: 4
4行目処理後: 5

表示: "Found 5 matching line" ← 実際は2行なのに
```

---

## 🟡 論理的問題

### 問題6: malloc/strcpyの実行タイミングの矛盾
```c
if (strncmp(buffer, SEARCH_PREFIX, PREFIX_LEN) == 0) {
    malloc_result = line_malloc(line, buffer, line_num);
}
// ...
strcpy(line[line_num], buffer);  // ← 常に実行
```

**根本的な設計ミス**:
- "From: "で始まる行だけ保存したいのに
- `strcpy`が全ての行で実行される
- 意図と実装が不一致

---

## 正しい実装例

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BUFFER_SIZE 1024
#define MAX_LINE 1000
#define SEARCH_PREFIX "From: "
#define PREFIX_LEN 6

int	main(int argc, char **argv)
{
	if (argc != 2) {
		fprintf(stderr, "Usage: %s <file>\n", argv[0]);
		return 1;
	}

	FILE *fp = fopen(argv[1], "r");
	if (fp == NULL) {
		fprintf(stderr, "Cannot open file\n");
		return 1;
	}

	char	buffer[BUFFER_SIZE];
	char	*line[MAX_LINE];
	int	match_count = 0;  // 一致した行数
	int	file_line_num = 0;  // ファイル内の行番号

	while (match_count < MAX_LINE && fgets(buffer, sizeof(buffer), fp) != NULL) {
		// "From: "で始まる行だけ保存
		if (strncmp(buffer, SEARCH_PREFIX, PREFIX_LEN) == 0) {
			line[match_count] = malloc(strlen(buffer) + 1);
			if (line[match_count] == NULL) {
				fprintf(stderr, "Memory allocation failed\n");
				// 既に確保したメモリを全て解放
				for (int i = 0; i < match_count; i++)
					free(line[i]);
				fclose(fp);
				return 1;
			}
			strcpy(line[match_count], buffer);
			match_count++;
		}

		// 行番号のカウント（長い行対応）
		size_t len = strlen(buffer);
		if (len > 0 && buffer[len - 1] == '\n') {
			file_line_num++;
		} else {
			// 行の続きを読み飛ばす
			int c;
			while ((c = fgetc(fp)) != EOF && c != '\n')
				;
			if (c == '\n')
				file_line_num++;
		}
	}
	fclose(fp);

	// 結果表示
	printf("=== Found %d matching lines ===\n", match_count);
	for (int i = 0; i < match_count; i++) {
		printf("%s", line[i]);
		free(line[i]);
	}

	return 0;
}
```

---

## エラーの重要度まとめ

| エラー | 重要度 | 症状 | 対処 |
|--------|--------|------|------|
| 1. 未初期化変数 | 🔴 致命的 | 未定義動作 | `= 0`で初期化 |
| 2-1. 未mallocへのstrcpy | 🔴 致命的 | セグフォルト | mallocとstrcpyを同じif内に |
| 2-2. インデックスずれ | 🔴 致命的 | セグフォルト/リーク | 0始まりに統一 |
| 3. move_fp関数 | 🟡 中程度 | 誤解を招く出力 | printfを削除 |
| 4. 関数設計 | 🟡 中程度 | 非効率 | malloc+strcpyを統合 |
| 5. カウント誤り | 🟡 軽度 | 間違った出力 | 別カウンタを用意 |
| 6. 論理矛盾 | 🔴 致命的 | 意図と実装の不一致 | 設計を見直す |

---

## 学習ポイント

1. **変数は必ず初期化する**
   ```c
   int result = 0;  // 必須
   ```

2. **配列のインデックスは0始まり**
   ```c
   for (int i = 0; i < count; i++)  // 標準パターン
   ```

3. **malloc/freeはペアで**
   - mallocした数だけfreeする
   - インデックスのずれはメモリリークの原因

4. **ポインタは使用前にmallocを確認**
   - 未初期化ポインタへのアクセスは危険

5. **関数の責任を明確に**
   - 「mallocだけ」「malloc+コピー」どちらか統一
