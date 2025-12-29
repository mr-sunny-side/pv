# WAVファイル読み取りプログラム `get_bin` 関数の再設計提案

## 現在の問題点

### 1. 型の乱用
- `float bit_per_sample` - これは整数であるべき（ビット数は常に整数）
- `float bit_per_second` - 大きな数値なのでfloatだと精度が不足する可能性
- `float duration` - これはfloatで良いが、計算過程で不要なキャストが多い
- 計算の途中で何度もキャストしていて、意図が不明確

### 2. 計算の流れが不明確
- `(bit_per_second / 8)` を何度も計算している（byte_rateそのもの）
- 型変換のタイミングが一貫していない
- どの時点でfloat→整数に変換すべきか明確でない

### 3. エラー値の返却方法
- `return -1`, `return 1`, `return bin_data` が混在
- エラー時と正常時で異なる型の値を返している

## 再設計の方針

### 基本原則
1. **整数で扱えるものは整数で扱う**
2. **浮動小数点が必要なのは「秒数」と「時間に関する計算」だけ**
3. **計算結果を使う直前に適切な型に変換する**
4. **同じ値を何度も計算しない**

### 型の使い分けルール

| 変数/計算 | 使うべき型 | 理由 |
|---------|----------|------|
| bit_depth, channel_num | uint16_t | WAVヘッダーの定義通り |
| sample_rate | uint32_t | WAVヘッダーの定義通り |
| byte_rate | uint32_t | WAVヘッダーの定義通り |
| bits_per_sample | uint32_t | bit_depth × channel_num（常に整数） |
| bytes_per_sample | uint32_t | bits_per_sample / 8（常に整数） |
| need_second | float | コマンドライン引数（小数可） |
| duration | float | data_size / byte_rate（小数になりうる） |
| byte_offset | uint32_t | byte_rate × need_second（計算後に整数化） |
| file_offset | long | fseek用（ファイル位置） |

## 推奨される実装

```c
int	get_bin(FILE *fp, FmtHeader *fmt, int data_size, long data_offset, float need_second) {

	// ステップ1: WAVフォーマット情報から基本的な定数を計算（全て整数）
	uint32_t	bits_per_sample = fmt->bit_depth * fmt->channel_num;
	uint32_t	bytes_per_sample = bits_per_sample / 8;
	uint32_t	byte_rate = fmt->byte_rate;  // 既にヘッダーにある

	// ステップ2: byte_rateの検証（念のため）
	if (byte_rate != fmt->sample_rate * bytes_per_sample) {
		fprintf(stderr, "Error: byte_rate validation failed\n");
		return -1;
	}
	fprintf(stderr, "byte_rate validation: OK\n");

	// ステップ3: ファイルの長さ（秒）を計算（浮動小数点が必要）
	float	duration = (float)data_size / (float)byte_rate;
	if (duration < need_second) {
		fprintf(stderr, "Error: need_second (%.2f) exceeds duration (%.2f)\n",
			need_second, duration);
		return -1;
	}

	// ステップ4: 指定秒数のバイトオフセットを計算
	// 重要: float計算を先に完了させてからuint32_tに変換
	uint32_t	byte_offset = (uint32_t)((float)byte_rate * need_second);

	// ステップ5: ファイル内の絶対位置を計算してシーク
	long	file_offset = data_offset + (long)byte_offset;
	if (fseek(fp, file_offset, SEEK_SET) != 0) {
		fprintf(stderr, "Error: fseek failed\n");
		return -1;
	}

	// ステップ6: 1サンプル分のデータを読み取る
	int	bin_data = 0;
	if (fread(&bin_data, bytes_per_sample, 1, fp) != 1) {
		fprintf(stderr, "Error: fread failed\n");
		return -1;
	}

	return bin_data;
}
```

## 設計のポイント

### 1. 計算の流れを明確に6ステップに分離
各ステップが何をしているか一目瞭然になります。

### 2. 変数名を意味のあるものに
- `bit_per_sample` → `bits_per_sample` (複数形で正確に)
- `bit_per_second` → 削除（`byte_rate`をそのまま使う）
- `result_offset` → `byte_offset` と `file_offset` に分離

### 3. 型変換のタイミングを明確化
```c
// 悪い例（現在）
long result_offset = data_offset + (long)((bit_per_second / 8) * need_second);
// 何をしているか分かりづらい

// 良い例（提案）
uint32_t byte_offset = (uint32_t)((float)byte_rate * need_second);
long file_offset = data_offset + (long)byte_offset;
// 1. byte_rateとneed_secondを掛ける（float計算）
// 2. uint32_tに変換（バイト数は正の整数）
// 3. data_offsetに加算してfile_offsetを得る（long型）
```

### 4. `byte_rate`を直接使用
`bit_per_second / 8` を何度も計算するのではなく、ヘッダーに既にある `byte_rate` を使います。

### 5. エラーハンドリングの統一
- 成功時: `bin_data`（0以上の値）を返す
- 失敗時: `-1` を返す（`return 1` は使わない）

## main関数の修正も必要

```c
// 176-181行目を以下に変更
float	need_second = atof(argv[2]);
int	bin_data = get_bin(fp, &fmt, data_size, data_offset, need_second);
if (bin_data < 0) {  // エラーチェックを簡潔に
	fprintf(stderr, "Error: get_bin failed\n");
	fclose(fp);
	return 1;
}
```

## なぜ bin: 0 が出力されるのか

現在の出力 `bin: 0` は、おそらく以下の理由です:

1. **オフセット計算は正しい**: 修正により正しい位置にシークできている
2. **読み取りバイト数の問題**: `result_read = (int)(bit_per_sample / 8)` で計算しているが、
   - `bit_per_sample` は `float` 型で 32.0（16bit × 2ch）
   - `32.0 / 8 = 4.0` → `(int)4` で4バイト
   - これは正しいはず
3. **freadの問題**: `fread(&bin_data, 4, 1, fp)` で4バイト読み取るが、
   - `bin_data` は `int` 型（通常4バイト）なのでサイズは問題なし
   - **しかし**: リトルエンディアン/ビッグエンディアンの問題かもしれない
   - または、その位置のサンプルが本当に0の可能性

### デバッグ用の追加

```c
// ステップ4の後に追加
fprintf(stderr, "Debug: byte_offset=%u, file_offset=%ld, bytes_per_sample=%u\n",
	byte_offset, file_offset, bytes_per_sample);

// ステップ6の後に追加
fprintf(stderr, "Debug: bin_data=0x%08X (hex)\n", bin_data);
```

これで実際にどのような値が読み取られているか確認できます。

## 学習ポイントまとめ

1. **型は目的に応じて使い分ける**: 整数・浮動小数点・符号の有無
2. **計算順序を意識する**: float計算を完了してから整数に変換
3. **同じ値を何度も計算しない**: 定数は変数に格納
4. **変数名は計算の意図を表す**: `result_offset` より `byte_offset` と `file_offset`
5. **エラーハンドリングを一貫させる**: 戻り値の意味を統一
6. **ステップを分けてコメントを書く**: デバッグしやすく、理解しやすい
