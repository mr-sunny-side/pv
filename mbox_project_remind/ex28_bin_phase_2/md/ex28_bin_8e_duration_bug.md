# WAV Duration計算エラーのデバッグ - 学習フィードバック

## 問題の症状

sample2.wavを解析したところ、durationが異常な値になった:

```bash
=== WAV File Information ===
Audio format: 1 (PCM)
Channels: 1 (Mono)
Sample rate: 44100 Hz
Bit per sample: 16
Duration: 6169.79  ← 期待値は 1.00 秒
```

## 問題のコード

### ex28_bin_8e.c:150
```c
float duration = (float)data_size / (bit_per_sample / 8 * fmt.sample_rate);
```

## 問題の原因

### 原因1: 演算子の優先順位と整数除算

C言語では `/` と `*` は**同じ優先順位**で、**左から右へ**評価されます:

```c
bit_per_sample / 8 * fmt.sample_rate
= (bit_per_sample / 8) * fmt.sample_rate
= (16 / 8) * 44100
= 2 * 44100
= 88200
```

一見正しそうですが、これは**偶然うまくいっているだけ**です。

### 原因2: 期待される計算式との不一致

**正しい計算式**:
```
duration (秒) = データサイズ(バイト) / バイトレート(バイト/秒)
```

**バイトレートの計算**:
```
バイトレート = サンプルレート × (ビット深度 ÷ 8) × チャンネル数
             = 44100 × (16 ÷ 8) × 1
             = 44100 × 2 × 1
             = 88200 バイト/秒
```

**期待される計算**:
```c
duration = data_size / (サンプルレート × バイト/サンプル)
         = data_size / (fmt.sample_rate × (bit_per_sample / 8))
```

### 原因3: 括弧の不足

現在のコード:
```c
(float)data_size / (bit_per_sample / 8 * fmt.sample_rate)
```

この括弧配置では:
1. `bit_per_sample / 8` が先に計算される（整数除算）
2. その結果に `fmt.sample_rate` が掛けられる
3. `data_size` がその結果で割られる

しかし、整数除算の順序や型によっては予期しない結果になる可能性があります。

## 実際に何が起きたか

Duration: 6169.79 という値から逆算すると:

```
6169.79 = data_size / x
x = data_size / 6169.79
```

もし data_size が期待通り 88200 なら:
```
x = 88200 / 6169.79 ≈ 14.29
```

これは明らかに `88200` (期待される分母) と異なります。

### 推測される原因

`data_size` の値が実際には異常に大きい可能性があります。

sample2.wav の実際の構造:
- fmt chunk: 24 bytes
- JUNK chunk: 143 bytes (スキップされるべき)
- LIST chunk: 41 bytes (スキップされるべき)
- data chunk: 88208 bytes (ヘッダ8バイト + データ88200バイト)

**可能性**: `data_size` に間違った値が入っている

計算してみると:
```
data_size = 6169.79 × 88200 ≈ 544,175,418
```

これは明らかに異常です。おそらく `data_size` 変数に正しい値が入っていない可能性が高いです。

## 根本原因の特定

もう一度コードを確認すると、`data_size` は `process_fread` 関数で設定されます:

```c
if (memcmp(tmp->chunk_id, "data", 4) == 0) {
    *data_size = tmp->chunk_size;
    *data_count = 1;
}
```

しかし、sample2.wav には:
1. fmt チャンク
2. JUNK チャンク ← これが誤って data_size に設定された？
3. LIST チャンク
4. data チャンク

**問題**: process_fread 関数に `else if` ではなく独立した `if` 文が必要かもしれません。

### コードを再確認

```c
if (memcmp(tmp->chunk_id, "fmt ", 4) == 0) {
    // fmt処理
}

if (memcmp(tmp->chunk_id, "data", 4) == 0) {  // ← これは else if であるべき？
    *data_size = tmp->chunk_size;
    *data_count = 1;
}
```

いいえ、これは問題ありません。各チャンクは独立して処理されます。

### 真の問題: 未知チャンクのスキップ忘れ

process_fread を見直すと、**未知チャンクをスキップする処理がない**ことがわかります！

```c
int process_fread(FILE *fp, FmtChunk *fmt, TmpChunk *tmp, ...) {
    if (fread(tmp, sizeof(*tmp), 1, fp) != 1) {
        return 1;
    }

    if (memcmp(tmp->chunk_id, "fmt ", 4) == 0) {
        // fmt処理
    }

    if (memcmp(tmp->chunk_id, "data", 4) == 0) {
        *data_size = tmp->chunk_size;
        *data_count = 1;
    }

    // ← 未知チャンク(JUNK, LIST)をスキップする処理がない！

    return 0;
}
```

**これが原因です！**

JUNKチャンクのヘッダを読んだ後、そのデータ部分（143バイト）をスキップせずに次の fread を実行すると、JUNKチャンクのデータの途中から読み込んでしまい、正しいチャンクヘッダが読めません。

## 解決方法

### 修正1: 未知チャンクのスキップ処理を追加

```c
int process_fread(FILE *fp, FmtChunk *fmt, TmpChunk *tmp,
                  int *fmt_count, int *data_count, uint32_t *data_size) {

    if (fread(tmp, sizeof(*tmp), 1, fp) != 1) {
        fprintf(stderr, "fread/process_fread: returned error\n");
        return 1;
    }

    if (memcmp(tmp->chunk_id, "fmt ", 4) == 0) {
        fseek(fp, -sizeof(*tmp), SEEK_CUR);
        if (fread(fmt, sizeof(*fmt), 1, fp) != 1)
            return 1;
        *fmt_count = 1;

        size_t fmt_data_size = sizeof(*fmt) - 8;
        if (fmt->chunk_size > fmt_data_size) {
            fseek(fp, (fmt->chunk_size - fmt_data_size), SEEK_CUR);
        }
    } else if (memcmp(tmp->chunk_id, "data", 4) == 0) {
        *data_size = tmp->chunk_size;
        *data_count = 1;
    } else {
        // 未知のチャンクをスキップ
        fseek(fp, tmp->chunk_size, SEEK_CUR);
        fprintf(stderr, "Unknown chunk '%c%c%c%c' skipped (%u bytes)\n",
                tmp->chunk_id[0], tmp->chunk_id[1],
                tmp->chunk_id[2], tmp->chunk_id[3],
                tmp->chunk_size);
    }

    return 0;
}
```

**重要**: `else if` と `else` の構造にして、必ず1つの処理だけが実行されるようにします。

### 修正2: Duration計算式の改善

より安全で読みやすい計算式にします:

#### オプションA: byte_rateを使用（最もシンプル）
```c
float duration = (float)data_size / fmt.byte_rate;
```

#### オプションB: 手動計算（学習目的）
```c
uint32_t bytes_per_sample = (fmt.bit_depth / 8) * fmt.channel_num;
uint32_t byte_rate = bytes_per_sample * fmt.sample_rate;
float duration = (float)data_size / byte_rate;
```

#### オプションC: 1行で明確に
```c
float duration = (float)data_size / ((fmt.bit_depth / 8) * fmt.channel_num * fmt.sample_rate);
```

**推奨**: オプションA（byte_rateを使用）

## 学んだ重要な概念

### 1. バイナリファイル解析の基本パターン

```c
while (条件) {
    // チャンクヘッダを読む
    fread(&header, sizeof(header), 1, fp);

    if (既知のチャンク) {
        // 処理する
    } else {
        // スキップする
        fseek(fp, header.size, SEEK_CUR);
    }
}
```

**必ず未知のチャンクをスキップする処理を入れる！**

### 2. if-else-if チェーンの重要性

```c
if (condition1) {
    // 処理1
} else if (condition2) {
    // 処理2
} else {
    // その他の処理（スキップなど）
}
```

複数の独立した `if` 文を使うと、複数の条件が同時に真になる可能性があるため、予期しない動作になります。

### 3. デバッグ時の確認ポイント

1. **変数の値を確認**: `printf` でデバッグ出力を追加
2. **計算式の各ステップを確認**: 中間値を出力
3. **ファイルポインタの位置を確認**: `ftell()` を使用
4. **期待値との比較**: 理論値と実際の値を比較

### 4. 整数演算の注意点

```c
// 悪い例: 精度損失の可能性
int result = a / b * c;

// 良い例: 括弧で明確に
int result = a / (b * c);

// より良い例: 型変換を明示
float result = (float)a / (b * c);
```

## 修正後の完全なコード例

```c
int process_fread(FILE *fp, FmtChunk *fmt, TmpChunk *tmp,
                  int *fmt_count, int *data_count, uint32_t *data_size) {

    if (fread(tmp, sizeof(*tmp), 1, fp) != 1) {
        fprintf(stderr, "fread/process_fread: returned error\n");
        return 1;
    }

    if (memcmp(tmp->chunk_id, "fmt ", 4) == 0) {
        fseek(fp, -sizeof(*tmp), SEEK_CUR);
        if (fread(fmt, sizeof(*fmt), 1, fp) != 1)
            return 1;
        *fmt_count = 1;

        size_t fmt_data_size = sizeof(*fmt) - 8;
        if (tmp->chunk_size > fmt_data_size) {
            fseek(fp, (tmp->chunk_size - fmt_data_size), SEEK_CUR);
        }
    } else if (memcmp(tmp->chunk_id, "data", 4) == 0) {
        *data_size = tmp->chunk_size;
        *data_count = 1;
    } else {
        // 未知のチャンクをスキップ
        fseek(fp, tmp->chunk_size, SEEK_CUR);
        fprintf(stderr, "Unknown chunk skipped\n");
    }

    return 0;
}

// main関数内
float duration = (float)data_size / fmt.byte_rate;
printf("Duration: %.2f seconds\n", duration);
```

## まとめ

### 成功のポイント
1. ✅ 未知チャンクを必ずスキップする
2. ✅ if-else-if 構造で排他的な処理を保証
3. ✅ 計算式は読みやすく、型安全に
4. ✅ デバッグ出力で値を確認

### 今後の応用
- 他のバイナリ形式でも同様の「スキップパターン」が重要
- チャンク解析は常に「知らないものをスキップ」する設計に
- 計算式は可読性と正確性を重視

---

**作成日**: 2025-12-27
**ファイル**: ex28_bin_8e.c
**学習テーマ**: バイナリチャンク解析、未知データのスキップ、Duration計算の罠
