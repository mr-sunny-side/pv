# Code Review: 11c_ex28_bin.c

**日付**: 2026-01-01
**レビュー対象**: [11c_ex28_bin.c](../11c_ex28_bin.c)
**目的**: 16bit PCM (stereo) WAVファイルの最大振幅とゼロクロス回数を表示する学習用プログラム

---

## Overview

16bit PCM (stereo) WAVファイルを解析し、各チャンネルの最大振幅とゼロクロス回数を表示する学習用プログラム。全体的によく構造化されていますが、いくつかの重要な問題があります。

---

## Critical Issues

### 1. ゼロクロスの定義が不正確

**場所**: [11c_ex28_bin.c:104-110](../11c_ex28_bin.c#L104-L110)

```c
void	conf_zero_cross(int *closs_count, int *bin_data) {
	if (bin_data[0] == 0)
		closs_count[0]++;
	if (bin_data[1] == 0)
		closs_count[1]++;
}
```

**問題点:**
- ゼロクロスは「符号が変わる点」をカウントするべきですが、現在は「値が0の点」をカウントしています
- 音響信号処理において、ゼロクロスは波形がゼロ軸を横切る（正→負 or 負→正）瞬間を意味します
- 正しくは前のサンプルと符号が反転した時にカウントすべきです

**推奨修正:**

```c
void	conf_zero_cross(int *cross_count, int *bin_data, int *prev_bin) {
	// 符号が変わったらカウント（正→負 or 負→正）
	if ((prev_bin[0] >= 0 && bin_data[0] < 0) ||
	    (prev_bin[0] < 0 && bin_data[0] >= 0))
		cross_count[0]++;
	if ((prev_bin[1] >= 0 && bin_data[1] < 0) ||
	    (prev_bin[1] < 0 && bin_data[1] >= 0))
		cross_count[1]++;

	// 次回の比較のために現在の値を保存
	prev_bin[0] = bin_data[0];
	prev_bin[1] = bin_data[1];
}
```

**main関数での使い方:**

```c
int	bin_data[2] = {0, 0};
int	max_bin[2] = {0, 0};
int	cross_count[2] = {0, 0};
int	prev_bin[2] = {0, 0};  // 前回のサンプル値を保存

while (1) {
	if (get_bin(fp, &fmt, bin_data) == -1) {
		if (feof(fp)) {
			fprintf(stderr, "get_bin/main: reached EOF\n");
			break;
		}
		fprintf(stderr, "ERROR get_bin/main: returned error\n");
		goto close_error;
	}
	conf_max_bin(max_bin, bin_data);
	conf_zero_cross(cross_count, bin_data, prev_bin);
}
```

---

### 2. Typo: "Closs" → "Cross"

**場所**: [11c_ex28_bin.c:210](../11c_ex28_bin.c#L210)

```c
printf("\nZero Closs Count:\n");  // Closs → Cross
```

**修正:**

```c
printf("\nZero Cross Count:\n");
```

また、関数パラメータ名も統一:

```c
void	conf_zero_cross(int *cross_count, int *bin_data, int *prev_bin)
```

---

### 3. コメントのチャンネル表記が逆

**場所**: [11c_ex28_bin.c:88-99](../11c_ex28_bin.c#L88-L99)

```c
int	get_bin(FILE *fp, const FmtChunk *fmt, int *bin_data) {
	int16_t		tmp_bin = 0;

	// 右チャンネル  ← これは間違い
	if (fread(&tmp_bin, fmt->bit_depth / 8, 1, fp) != 1) {
		fprintf(stderr, "ERROR fread/get_bin: Cannot read file\n");
		return -1;
	}
	bin_data[0] = (int)tmp_bin;  // bin_data[0]は左チャンネル

	if (fread(&tmp_bin, fmt->bit_depth / 8, 1, fp) != 1) {
		fprintf(stderr, "ERROR fread/get_bin: Cannot read file\n");
		return -1;
	}
	bin_data[1] = (int)tmp_bin;

	return 0;
}
```

**修正:**

```c
int	get_bin(FILE *fp, const FmtChunk *fmt, int *bin_data) {
	int16_t		tmp_bin = 0;

	// 左チャンネル
	if (fread(&tmp_bin, fmt->bit_depth / 8, 1, fp) != 1) {
		fprintf(stderr, "ERROR fread/get_bin: Cannot read file\n");
		return -1;
	}
	bin_data[0] = (int)tmp_bin;

	// 右チャンネル
	if (fread(&tmp_bin, fmt->bit_depth / 8, 1, fp) != 1) {
		fprintf(stderr, "ERROR fread/get_bin: Cannot read file\n");
		return -1;
	}
	bin_data[1] = (int)tmp_bin;

	return 0;
}
```

---

## Code Quality Issues

### 4. `conf_max_bin`が入力を破壊している

**場所**: [11c_ex28_bin.c:112-125](../11c_ex28_bin.c#L112-L125)

```c
void	conf_max_bin(int *max_bin, int *bin_data) {
	// 振幅データを絶対値に変換
	if (bin_data[0] < 0)
		bin_data[0] *= -1;  // bin_dataを変更している！
	if (bin_data[1] < 0)
		bin_data[1] *= -1;

	// 最大振幅を更新
	if (max_bin[0] < bin_data[0])
		max_bin[0] = bin_data[0];
	if (max_bin[1] < bin_data[1])
		max_bin[1] = bin_data[1];
}
```

**問題点:**
- `bin_data`を直接変更してしまうため、後続の処理で使う値が壊れます
- 現在のコードでは`conf_max_bin`を先に呼んでいるため、もし`conf_zero_cross`が正しく実装されても、符号情報が失われて正しく動作しません
- 関数は副作用を最小限にすべきです

**推奨修正:**

```c
void	conf_max_bin(int *max_bin, const int *bin_data) {
	// ローカル変数で絶対値を計算（入力を破壊しない）
	int abs_l = bin_data[0] < 0 ? -bin_data[0] : bin_data[0];
	int abs_r = bin_data[1] < 0 ? -bin_data[1] : bin_data[1];

	if (max_bin[0] < abs_l)
		max_bin[0] = abs_l;
	if (max_bin[1] < abs_r)
		max_bin[1] = abs_r;
}
```

または標準ライブラリの`abs()`を使用:

```c
void	conf_max_bin(int *max_bin, const int *bin_data) {
	int abs_l = abs(bin_data[0]);
	int abs_r = abs(bin_data[1]);

	if (max_bin[0] < abs_l)
		max_bin[0] = abs_l;
	if (max_bin[1] < abs_r)
		max_bin[1] = abs_r;
}
```

**注意**: `const int *bin_data`にすることで、関数内で`bin_data`を変更できないようにコンパイラが保証してくれます。

---

## Minor Issues

### 5. FmtChunkのサイズ計算ロジック

**場所**: [11c_ex28_bin.c:54-62](../11c_ex28_bin.c#L54-L62)

```c
uint32_t	skip_size = fmt->chunk_size - (uint32_t)sizeof(FmtChunk);
if (sizeof(FmtChunk) < fmt->chunk_size) {
	if (fseek(fp, skip_size, SEEK_CUR) != 0) {
		fprintf(stderr, "ERROR fseek/process_read: Cannot skip remaining fmt data\n");
		return -1;
	}
	fprintf(stderr, "process_read: Remaining fmt data is skipped\n");
}
```

**問題点:**
- `skip_size`の計算が条件判定の前にあるため、`fmt->chunk_size < sizeof(FmtChunk)`の場合にアンダーフローする可能性があります
- `sizeof(FmtChunk)`は構造体全体（20バイト）ですが、`fmt->chunk_size`には`chunk_id`(4バイト)と`chunk_size`(4バイト)自体は含まれません

**正しい計算:**

WAVファイルのチャンク構造:
```
chunk_id     (4 bytes)  ← sizeof(FmtChunk)に含まれる
chunk_size   (4 bytes)  ← sizeof(FmtChunk)に含まれる
<data>       (chunk_size bytes)  ← これがchunk_sizeの値
```

`sizeof(FmtChunk) = 20`ですが、これには`chunk_id`(4) + `chunk_size`(4)が含まれているので、実際のデータ部分は`sizeof(FmtChunk) - 8 = 12`バイトです。

**推奨修正:**

```c
// FmtChunkのデータ部分のサイズ（chunk_idとchunk_sizeを除く）
uint32_t fmt_data_size = sizeof(FmtChunk) - 8;

if (fmt->chunk_size > fmt_data_size) {
	uint32_t skip_size = fmt->chunk_size - fmt_data_size;
	if (fseek(fp, skip_size, SEEK_CUR) != 0) {
		fprintf(stderr, "ERROR fseek/process_read: Cannot skip remaining fmt data\n");
		return -1;
	}
	fprintf(stderr, "process_read: Remaining fmt data is skipped (%u bytes)\n", skip_size);
}
```

---

## Positive Points

以下の点は非常に良い実装です:

✅ **構造体のパッキング制御**
- `#pragma pack(push, 1)`で構造体のパディングを正しく制御し、バイナリデータと完全に一致させています

✅ **符号付きデータの正しい読み込み**
- `int16_t`を使って符号付き16bitデータを正しく読み込んでいます
- これは11aで指摘された`uint16_t`の問題を完全に修正しています

✅ **エラーハンドリング**
- EOF判定を適切に行っています
- `goto`文を使った統一的なクリーンアップ処理（`close_error`ラベル）

✅ **柔軟なWAVチャンクパーサー**
- LISTチャンクなどの未知のチャンクを適切にスキップしています
- 実際のWAVファイルには様々な拡張チャンクが含まれることがあるため、これは重要です

✅ **デバッグメッセージ**
- `fprintf(stderr, ...)`による詳細なデバッグ出力で、処理の流れが追跡しやすくなっています

---

## Security & Performance

### セキュリティ
- ✅ **メモリリーク**: なし
- ✅ **バッファオーバーフロー**: `fread`のサイズ指定が適切
- ✅ **NULLチェック**: `fopen`の返り値を適切にチェック
- ✅ **整数オーバーフロー**: 基本的に問題なし（ただし、FmtChunkのサイズ計算は要注意）

### パフォーマンス
- 学習用途として適切
- サンプルごとに関数呼び出しを行っていますが、小規模なWAVファイルであれば問題なし

---

## Summary Table

| 優先度 | 項目 | 場所 | 内容 |
|--------|------|------|------|
| 🔴 High | ゼロクロスロジック | L104-110 | 「値が0」ではなく「符号の変化」を検出すべき |
| 🔴 High | データ破壊 | L112-125 | `conf_max_bin`が`bin_data`を変更している |
| 🟡 Medium | Typo修正 | L210, L104 | "Closs" → "Cross" |
| 🟡 Medium | コメント修正 | L88 | チャンネル表記が逆（右→左） |
| 🟢 Low | サイズ計算 | L54-62 | FmtChunkのサイズ計算を修正 |
| 🟢 Low | コード改善 | L112-125 | `abs()`関数の使用を検討 |

---

## Conclusion

学習用コードとして非常に良い構造をしていますが、**ゼロクロスの実装が音響信号処理の定義と異なる**という重要な問題があります。

ゼロクロスは音響信号処理において基本的な特徴量の一つで、以下のような用途があります:
- **音声/非音声の判定**: 音声部分はゼロクロス率が低く、無音や雑音は高い
- **有声音/無声音の分類**: 「あ」などの有声音は低く、「す」などの無声音は高い
- **ピッチ推定**: ゼロクロス率から大まかな周波数を推定できる

この定義を正しく実装することで、より実践的な音響解析ツールになります。

また、`conf_max_bin`が入力データを破壊する問題も、バグの原因となりやすいので修正を推奨します。

---

**Generated**: 2026-01-01
**Reviewer**: Claude Sonnet 4.5
