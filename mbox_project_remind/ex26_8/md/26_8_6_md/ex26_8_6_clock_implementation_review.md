# Code Review: ex26_8_6.c - clock()による処理速度測定

## 概要
このプログラムは、.mboxファイルから"From: "で始まる行を抽出し、メールアドレスを表示するツールです。
**重要な新機能**として、`clock()`関数を使った処理速度測定が実装されています。これはPythonでの同等実装と処理速度を比較するための準備段階です。

**レビューの目的**: 学習目的 - `clock()`関数の正しい使い方と時間測定のベストプラクティス
**対象ファイル**: .mboxファイル
**測定対象**: ファイル処理全体のCPU時間

## コード品質分析

### ✅ 良い点

#### 1. **機能の分離**
```c
void count_line(FILE *fp)  // 43-53行目
{
    char c;
    while ((c = fgetc(fp)) != EOF && c != '\n')
        ;
}
```
- 長い行をスキップする処理を独立した関数に分離
- 再利用可能で読みやすいコード構造

#### 2. **適切なコメント**
```c
// 到達していない場合、fpのポインタをそこまで進める
// 動かすのはfget関数が返すファイル構造体のポインタなので
    // fpを動かすわけでは無い。よってasteriskは1つ
```
- ポインタの動作について詳しく説明
- 学習中の思考プロセスが記録されている

#### 3. **エラーハンドリング**
```c
if (ext_sender_and_copy(buffer, &email) == 1) {
    fprintf(stderr, "Cannot extract email\n");
    free(email);
    fclose(fp);
    return 1;
}
```
- メール抽出失敗時の適切な処理
- リソース解放も考慮している

#### 4. **統計情報の出力先**
```c
// 標準出力への表示を制限している
fprintf(stderr, "=== Statistics ===\n");
fprintf(stderr, "\nTotal Lines: %d\n", line_num);
fprintf(stderr, "Prosessing Time: %.3f s\n", cpu_time);
```
- 統計情報を標準エラー出力（stderr）に出力
- これにより標準出力のデータをパイプやリダイレクトで処理可能
- 良い設計判断です！

### 🔴 重大な問題

#### 1. **型エラー: `time_t` vs `clock_t`（74, 99行目）**

```c
// ❌ 間違い
time_t start_time = clock();  // 74行目
time_t end_time = clock();    // 99行目
double cpu_time = ((double)(end_time - start_time)) / CLOCKS_PER_SEC;
```

**問題点**:
- `clock()`の戻り値は`clock_t`型であり、`time_t`型ではありません
- これは**型の誤用**で、コンパイラ警告の原因となります
- 場合によっては正しく動作しないリスクがあります

**`clock_t` と `time_t` の違い**:

| 型 | 用途 | 関連関数 | 精度 |
|---|---|---|---|
| `clock_t` | **CPU時間**（プロセスがCPUを使用した時間） | `clock()` | マイクロ秒レベル |
| `time_t` | **実時間**（wall-clock time、カレンダー時刻） | `time()`, `difftime()` | 秒単位 |

**正しい実装**:
```c
// ✅ 正しい
clock_t start_time = clock();  // clock_t型を使用
clock_t end_time = clock();
double cpu_time = ((double)(end_time - start_time)) / CLOCKS_PER_SEC;
```

**なぜこの違いが重要か**:
```c
// CPU時間の例: プログラムが0.5秒CPUを使用、合計3秒待機した場合
clock_t cpu = clock();  // → 0.5秒分のクロックティック
time_t wall = time();   // → 3秒経過

// ファイルI/O処理では違いが顕著に現れる
// - clock(): 実際の処理時間を測定（ディスク待ち時間は含まない）
// - time(): 開始から終了までの経過時間（待ち時間含む）
```

#### 2. **タイプミス（105行目）**

```c
// ❌ タイポ
fprintf(stderr, "Prosessing Time: %.3f s\n", cpu_time);

// ✅ 正しい
fprintf(stderr, "Processing Time: %.3f s\n", cpu_time);
```

### ⚠️ 改善が望ましい点

#### 1. **メモリ管理の安全性（88-92行目）**

```c
if (ext_sender_and_copy(buffer, &email) == 1) {
    fprintf(stderr, "Cannot extract email\n");
    free(email);  // ⚠️ emailの状態が不定
    fclose(fp);
    return 1;
}
```

**問題点**:
- `ext_sender_and_copy()`が失敗した場合、`email`が以下のいずれかの状態:
  1. `malloc()`前の失敗 → `email`は未初期化（NULLでない可能性）
  2. `malloc()`後の失敗 → `email`は有効なポインタ

**安全な実装**:
```c
// 方法1: 関数側で責任を持つ
int ext_sender_and_copy(char *from_line, char **email)
{
    char *start = NULL;
    char *end = NULL;

    *email = NULL;  // 最初にNULLで初期化

    // ... 検証処理 ...

    int interval = end - start;
    *email = malloc(interval + 1);
    if (*email == NULL)
        return 1;

    strncpy(*email, start, interval);
    (*email)[interval] = '\0';
    return 0;
}

// 方法2: main()側で初期化
char *email = NULL;  // 初期化
while (fgets(buffer, sizeof(buffer), fp) != NULL) {
    // ...
    if (ext_sender_and_copy(buffer, &email) == 1) {
        fprintf(stderr, "Cannot extract email\n");
        if (email != NULL)  // NULLチェック
            free(email);
        fclose(fp);
        return 1;
    }
    printf("%d: %s\n", line_num, email);
    free(email);
    email = NULL;  // free後にNULL代入（安全性向上）
}
```

#### 2. **定数の一元管理**

現在の実装は良好ですが、さらに改善するなら:
```c
#define BUFFER_SIZE 1024
#define SEARCH_PREFIX "From: "
#define PREFIX_LEN 6
#define OUTPUT_FORMAT "%d: %s\n"  // 出力形式も定数化

// 使用例
printf(OUTPUT_FORMAT, line_num, email);
```

#### 3. **行番号カウントの正確性**

現在の実装（79-84行目）では長い行を正しく処理していますが、行番号は**バッファ読み込み回数**でカウントされています:

```c
while (fgets(buffer, sizeof(buffer), fp) != NULL) {
    size_t len = strlen(buffer);
    if (len > 0 && buffer[len - 1] != '\n')
        count_line(fp);
    line_num++;  // fgets()の呼び出しごとにインクリメント
    // ...
}
```

これは長い行がある場合、以下のように動作します:
- 1行が2000バイト → `fgets()`を2回呼び出す → line_num += 2
- 実際のファイル行数とずれる可能性

**もし実際の行数をカウントしたい場合**:
```c
while (fgets(buffer, sizeof(buffer), fp) != NULL) {
    // ... 処理 ...

    size_t len = strlen(buffer);
    if (len > 0 && buffer[len - 1] == '\n') {
        line_num++;  // 改行がある時だけインクリメント
    } else {
        count_line(fp);
        line_num++;  // 長い行の最後でもインクリメント
    }
}
```

ただし、**現在の実装でも用途によっては問題ない**場合があります（処理単位としてのカウント）。

## clock()の正しい使用方法

### clock_t型とCLOCKS_PER_SECマクロ

#### clock()関数の基本
```c
#include <time.h>

clock_t clock(void);
```

**仕様**:
- プロセスがCPUを使用した時間を測定
- 戻り値: プログラム開始からのCPUクロック数（`clock_t`型）
- エラー時: `(clock_t)-1`を返す

#### CLOCKS_PER_SEC マクロ
```c
// time.hで定義
#define CLOCKS_PER_SEC 1000000  // 例: Linuxではマイクロ秒単位
```

**意味**: 1秒あたりのクロックティック数
- Linux/POSIX: 通常 `1000000` (1秒 = 100万クロック)
- Windows: 通常 `1000` (1秒 = 1000クロック)
- 環境によって異なるため、必ずこのマクロで除算する

#### 正しい使用パターン
```c
#include <time.h>
#include <stdio.h>

int main(void)
{
    clock_t start_time, end_time;
    double cpu_time_used;

    start_time = clock();  // 測定開始

    // === 測定対象の処理 ===
    for (int i = 0; i < 1000000; i++) {
        // 何か処理
    }

    end_time = clock();  // 測定終了

    // 秒単位に変換
    cpu_time_used = ((double)(end_time - start_time)) / CLOCKS_PER_SEC;

    printf("CPU Time: %.3f seconds\n", cpu_time_used);

    return 0;
}
```

### CPU時間 vs 実時間（Wall-Clock Time）

#### 違いの理解
```c
#include <time.h>

// CPU時間（プロセスがCPUを実際に使った時間）
clock_t cpu_start = clock();
// ... 処理 ...
clock_t cpu_end = clock();
double cpu_time = (double)(cpu_end - cpu_start) / CLOCKS_PER_SEC;

// 実時間（開始から終了までの経過時間）
time_t wall_start = time(NULL);
// ... 処理 ...
time_t wall_end = time(NULL);
double wall_time = difftime(wall_end, wall_start);
```

#### I/Oバウンド処理での違い

.mboxファイル処理のような**I/Oバウンド**な処理では、2つの時間に大きな差が出ます:

```c
// 例: 1GBのファイルを読み込む処理
clock_t cpu_start = clock();
time_t wall_start = time(NULL);

FILE *fp = fopen("large.mbox", "r");
char buffer[1024];
while (fgets(buffer, sizeof(buffer), fp) != NULL) {
    // ディスクからデータ読み込み（I/O待ち発生）
}
fclose(fp);

clock_t cpu_end = clock();
time_t wall_end = time(NULL);

double cpu_time = (double)(cpu_end - cpu_start) / CLOCKS_PER_SEC;
double wall_time = difftime(wall_end, wall_start);

// 結果の例:
// CPU Time: 0.250 seconds   <- CPUが実際に処理した時間
// Wall Time: 5.000 seconds  <- 開始から終了までの時間（I/O待ち含む）
```

**どちらを使うべきか**:
- **`clock()` (CPU時間)**: アルゴリズムの効率比較、純粋な処理速度測定
- **`time()` (実時間)**: ユーザー体感時間、全体のパフォーマンス測定

**このプログラムでは**: CとPythonの処理効率を比較するため、`clock()`の使用は適切です！

### エラーチェックの追加
```c
clock_t start_time = clock();
if (start_time == (clock_t)-1) {
    fprintf(stderr, "Error: clock() failed\n");
    return 1;
}

// ... 処理 ...

clock_t end_time = clock();
if (end_time == (clock_t)-1) {
    fprintf(stderr, "Error: clock() failed\n");
    return 1;
}

// オーバーフローチェック
if (end_time < start_time) {
    fprintf(stderr, "Warning: Clock overflow detected\n");
}

double cpu_time = ((double)(end_time - start_time)) / CLOCKS_PER_SEC;
```

## Python比較のための推奨事項

### 1. Pythonでの対応する時間測定方法

Pythonには複数の時間測定方法があります:

#### time.time() - 実時間（wall-clock）
```python
import time

start_time = time.time()
# ... 処理 ...
end_time = time.time()
elapsed_time = end_time - start_time
print(f"Wall Time: {elapsed_time:.3f} seconds")
```
- C言語の`time()`に相当
- システム時刻を使用（時刻変更の影響を受ける）

#### time.process_time() - CPU時間（推奨）
```python
import time

start_time = time.process_time()
# ... 処理 ...
end_time = time.process_time()
cpu_time = end_time - start_time
print(f"CPU Time: {cpu_time:.3f} seconds")
```
- **C言語の`clock()`に相当** ← これを使用すべき
- プロセスのCPU時間を測定
- sleep()やI/O待ち時間は含まない

#### time.perf_counter() - 高精度実時間
```python
import time

start_time = time.perf_counter()
# ... 処理 ...
end_time = time.perf_counter()
elapsed_time = end_time - start_time
print(f"High-Res Time: {elapsed_time:.6f} seconds")
```
- 最も精度が高い（ナノ秒レベル）
- ベンチマークに適している

### 2. Python実装の推奨コード例

C言語版と公平に比較するための推奨実装:

```python
#!/usr/bin/env python3
import sys
import time
import re

def extract_sender(line):
    """Extract email address from 'From: ' line"""
    # Pattern 1: Name <email@example.com>
    match = re.search(r'<([^>]+)>', line)
    if match:
        return match.group(1)

    # Pattern 2: From: email@example.com
    parts = line.split(None, 1)
    if len(parts) >= 2:
        return parts[1].strip()

    return None

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <mbox_file>", file=sys.stderr)
        sys.exit(1)

    file_name = sys.argv[1]

    # === 測定開始 ===
    start_time = time.process_time()  # CPU時間測定（C言語のclock()に対応）

    try:
        with open(file_name, 'r', encoding='utf-8', errors='ignore') as fp:
            line_num = 0
            for line in fp:
                line_num += 1
                if line.startswith("From: "):
                    email = extract_sender(line)
                    if email:
                        print(f"{line_num}: {email}")

    except FileNotFoundError:
        print(f"Error: Cannot open file '{file_name}'", file=sys.stderr)
        sys.exit(1)

    # === 測定終了 ===
    end_time = time.process_time()
    cpu_time = end_time - start_time

    # 統計情報（stderrに出力してC版と統一）
    print("=== Statistics ===", file=sys.stderr)
    print(f"\nTotal Lines: {line_num}", file=sys.stderr)
    print(f"Processing Time: {cpu_time:.3f} s", file=sys.stderr)

if __name__ == "__main__":
    main()
```

### 3. 比較時の注意点

#### I/OバウンドとCPUバウンドの違い

**このプログラムはI/Oバウンド**です:
```
処理の割合:
- ファイル読み込み（I/O）: 95%
- 文字列処理（CPU）: 5%
```

**測定結果の解釈**:
```bash
# C言語版
$ ./ex26_8_6 large.mbox 2>&1 | tail -3
=== Statistics ===
Total Lines: 100000
Processing Time: 0.234 s  # CPU時間

# Python版
$ python3 ex26_8_6.py large.mbox 2>&1 | tail -3
=== Statistics ===
Total Lines: 100000
Processing Time: 0.456 s  # CPU時間
```

**解釈**:
- CPU時間での比較 → **処理効率**の違いを測定
- Cの方が速い理由: 文字列処理、メモリ管理がネイティブ
- ただしI/Oバウンドなため、差は小さい可能性がある

#### 公平な比較のためのチェックリスト

✅ **同じ測定方法を使用**:
- C: `clock()` (CPU時間)
- Python: `time.process_time()` (CPU時間)

✅ **同じ出力形式**:
- 両方とも統計情報をstderrに出力
- フォーマットを統一

✅ **同じファイルでテスト**:
- 同じ.mboxファイルを使用
- ファイルキャッシュの影響に注意

✅ **複数回測定**:
```bash
# 3回測定して平均を取る
for i in {1..3}; do
    ./ex26_8_6 test.mbox 2>&1 | grep "Processing Time"
done
```

❌ **避けるべき比較**:
- 異なる測定方法（CPU時間 vs 実時間）
- 異なる最適化レベル（C側だけ-O2でコンパイル等）
- キャッシュされたファイル vs 初回読み込み

### 4. 出力形式の統一

両方の言語で同じフォーマットを使用すると比較が容易です:

```c
// C言語版
fprintf(stderr, "=== Statistics ===\n");
fprintf(stderr, "Total Lines: %d\n", line_num);
fprintf(stderr, "Processing Time: %.3f s\n", cpu_time);
fprintf(stderr, "Measurement: CPU time (clock())\n");
```

```python
# Python版
print("=== Statistics ===", file=sys.stderr)
print(f"Total Lines: {line_num}", file=sys.stderr)
print(f"Processing Time: {cpu_time:.3f} s", file=sys.stderr)
print("Measurement: CPU time (process_time())", file=sys.stderr)
```

## 改善版コード例

以下は、全ての問題を修正した完全版です:

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define BUFFER_SIZE 1024
#define SEARCH_PREFIX "From: "
#define PREFIX_LEN 6

void print_help(char *prog_name)
{
	printf("=== How to Use ===\n");
	printf("[%s] [mbox File]\n", prog_name);
	printf("\nThis program will extract sender emails from an mbox file\n");
	printf("and measure processing time for performance comparison.\n");
	printf("command '-h' or '--help' to show this message\n");
}

int ext_sender_and_copy(char *from_line, char **email)
{
	char *start = NULL;
	char *end = NULL;

	/* 最初にNULLで初期化（安全性向上） */
	*email = NULL;

	if ((start = strchr(from_line, '<')) != NULL) {
		start++;
		if ((end = strchr(start, '>')) == NULL)
			return 1;
	} else if ((start = strchr(from_line, ' ')) != NULL) {
		start++;
		if ((end = strchr(start, '\n')) == NULL)
			return 1;
	} else {
		return 1;
	}

	int interval = end - start;
	*email = malloc(interval + 1);
	if (*email == NULL)
		return 1;

	strncpy(*email, start, interval);
	(*email)[interval] = '\0';
	return 0;
}

void count_line(FILE *fp)
{
	/* 長い行の残りをスキップ */
	char c;
	while ((c = fgetc(fp)) != EOF && c != '\n')
		;
}

int main(int argc, char **argv)
{
	if (argc != 2) {
		fprintf(stderr, "Argument Error\n");
		fprintf(stderr, "Usage: %s <mbox_file>\n", argv[0]);
		return 1;
	}

	if (strcmp(argv[1], "-h") == 0 || strcmp(argv[1], "--help") == 0) {
		print_help(argv[0]);
		return 0;
	}

	const char *file_name = argv[1];
	FILE *fp = fopen(file_name, "r");
	if (fp == NULL) {
		fprintf(stderr, "Cannot Open File: %s\n", file_name);
		return 1;
	}

	/* ✅ 修正: clock_t型を使用 */
	clock_t start_time = clock();
	if (start_time == (clock_t)-1) {
		fprintf(stderr, "Error: clock() failed\n");
		fclose(fp);
		return 1;
	}

	char buffer[BUFFER_SIZE];
	char *email = NULL;  /* 初期化 */
	int line_num = 0;

	while (fgets(buffer, sizeof(buffer), fp) != NULL) {
		size_t len = strlen(buffer);

		/* 長い行の処理 */
		if (len > 0 && buffer[len - 1] != '\n')
			count_line(fp);
		line_num++;

		/* "From: "で始まる行を処理 */
		if (strncmp(buffer, SEARCH_PREFIX, PREFIX_LEN) == 0) {
			if (ext_sender_and_copy(buffer, &email) == 1) {
				fprintf(stderr, "Cannot extract email at line %d\n", line_num);
				/* emailはNULLで初期化されているので安全 */
				if (email != NULL)
					free(email);
				fclose(fp);
				return 1;
			}
			printf("%d: %s\n", line_num, email);
			free(email);
			email = NULL;  /* free後にNULL代入 */
		}
	}

	/* ✅ 修正: clock_t型を使用 */
	clock_t end_time = clock();
	if (end_time == (clock_t)-1) {
		fprintf(stderr, "Error: clock() failed\n");
		fclose(fp);
		return 1;
	}

	/* CPU時間を計算 */
	double cpu_time = ((double)(end_time - start_time)) / CLOCKS_PER_SEC;

	/* 統計情報を標準エラー出力に表示 */
	fprintf(stderr, "=== Statistics ===\n");
	fprintf(stderr, "Total Lines: %d\n", line_num);
	fprintf(stderr, "Processing Time: %.3f s\n", cpu_time);  /* ✅ タイポ修正 */
	fprintf(stderr, "Measurement: CPU time (clock())\n");

	fclose(fp);
	return 0;
}
```

### 主な修正点

1. **型エラー修正（74, 99, 100行目）**:
   ```c
   time_t start_time = clock();  // ❌
   clock_t start_time = clock();  // ✅
   ```

2. **タイポ修正（105行目）**:
   ```c
   "Prosessing Time"  // ❌
   "Processing Time"  // ✅
   ```

3. **メモリ管理改善**:
   ```c
   *email = NULL;  // 関数内で初期化
   char *email = NULL;  // main()でも初期化
   email = NULL;  // free()後にNULL代入
   ```

4. **エラーチェック追加**:
   ```c
   if (start_time == (clock_t)-1) { /* エラー処理 */ }
   ```

5. **測定方法の明示**:
   ```c
   fprintf(stderr, "Measurement: CPU time (clock())\n");
   ```

## 学習ポイント

### 1. 型の正しい選択

**重要**: 関数の戻り値型を正しく使用する

```c
// 時間関連の型の使い分け
clock_t   cpu_time;      // clock()の戻り値
time_t    calendar_time; // time()の戻り値
struct tm *time_struct;  // localtime()の戻り値
```

**間違った型を使うとどうなるか**:
- コンパイラ警告（型の不一致）
- プラットフォーム依存の問題
- 将来のコード保守性の低下

### 2. 時間測定の目的に応じた選択

| 目的 | 使用する関数 | 測定内容 |
|-----|------------|---------|
| アルゴリズムの効率比較 | `clock()` | CPU時間 |
| ユーザー体感時間 | `time()` | 実時間 |
| 高精度ベンチマーク | `gettimeofday()` (POSIX) | マイクロ秒精度 |

**このプログラムの場合**:
- 目的: CとPythonの処理効率比較
- 最適: `clock()` でCPU時間を測定 ✅

### 3. CPU時間 vs 実時間の理解

```c
/* 例: sleep()を含む処理 */
clock_t cpu_start = clock();
time_t wall_start = time(NULL);

sleep(2);  // 2秒間スリープ

clock_t cpu_end = clock();
time_t wall_end = time(NULL);

// CPU時間: 約0秒（CPUを使っていない）
// 実時間: 約2秒（経過した時間）
```

**I/Oバウンド処理での意味**:
- ファイル読み込み待ち時間は**CPU時間に含まれない**
- `clock()`は純粋な処理効率を測定できる

### 4. クロスプラットフォーム考慮事項

```c
/* CLOCKS_PER_SECはプラットフォーム依存 */
#ifdef __linux__
    // Linux: 通常 1000000
#elif _WIN32
    // Windows: 通常 1000
#endif

/* だから必ずCLOCKS_PER_SECマクロを使う */
double cpu_time = (double)(end - start) / CLOCKS_PER_SEC;  // ✅ 正しい

/* ハードコーディングは絶対にNG */
double cpu_time = (double)(end - start) / 1000000;  // ❌ 環境依存
```

### 5. ベンチマークのベストプラクティス

#### 複数回測定
```c
#define NUM_RUNS 5

clock_t total_time = 0;
for (int i = 0; i < NUM_RUNS; i++) {
    clock_t start = clock();

    /* 測定対象の処理 */

    clock_t end = clock();
    total_time += (end - start);
}

double avg_time = ((double)total_time / NUM_RUNS) / CLOCKS_PER_SEC;
printf("Average CPU Time: %.3f s\n", avg_time);
```

#### ウォームアップラン
```c
/* 最初の1回はキャッシュウォームアップとして除外 */
process_file(filename);  // ウォームアップ

clock_t start = clock();
process_file(filename);  // 実測定
clock_t end = clock();
```

## 次のステップ: Python実装の作成

### 1. Pythonスクリプトの作成

**ファイル名**: `ex26_8_6.py` （C版と対応させる）

**実装のポイント**:
```python
import time

# CPU時間測定（C言語のclock()に対応）
start_time = time.process_time()

# ... ファイル処理 ...

end_time = time.process_time()
cpu_time = end_time - start_time

# C版と同じフォーマットで出力
print(f"Processing Time: {cpu_time:.3f} s", file=sys.stderr)
```

### 2. 比較実験の実施

```bash
# 同じファイルで両方を実行
mbox_file="test.mbox"

# C言語版（コンパイル）
gcc -o ex26_8_6 ex26_8_6.c -std=c99 -Wall
./ex26_8_6 "$mbox_file" 2>&1 | grep "Processing Time"

# Python版
python3 ex26_8_6.py "$mbox_file" 2>&1 | grep "Processing Time"
```

### 3. 結果の分析観点

**予想される結果**:
- C言語: 0.1〜0.5秒（ファイルサイズによる）
- Python: 0.3〜1.0秒（C言語の2〜3倍程度）

**差が出る理由**:
1. 文字列処理: Cはネイティブ、Pythonはオーバーヘッドあり
2. メモリ管理: Cは手動、Pythonは自動（GCのコスト）
3. 型チェック: Cはコンパイル時、Pythonは実行時

**ただし**: I/Oバウンドなため、差は思ったより小さい可能性がある

### 4. 学習目標の確認

✅ `clock()`関数の正しい使い方を理解
✅ CPU時間と実時間の違いを理解
✅ C言語とPythonの性能比較手法を習得
✅ ベンチマーク測定の注意点を学習

## まとめ

### 主要な修正事項
1. **`time_t` → `clock_t`**: 型エラーの修正
2. **"Prosessing" → "Processing"**: タイポ修正
3. **メモリ管理**: NULL初期化と安全性向上
4. **エラーチェック**: `clock()`の戻り値検証

### 現在のコードの評価
- **機能性**: ✅ 正しく動作（型エラー修正後）
- **コード品質**: ✅ 良好（コメント、関数分離）
- **測定方法**: ✅ 適切（CPU時間測定）
- **Python比較準備**: ✅ 良い設計

### 学習成果
このコードを通じて以下を学びました:
- `clock()`を使った処理時間測定
- `clock_t`型の正しい使用方法
- CPU時間と実時間の違い
- I/Oバウンド処理における測定の意味
- 言語間性能比較のベストプラクティス

次のステップとして、Pythonで同等の機能を実装し、実際に性能を比較してみてください！
