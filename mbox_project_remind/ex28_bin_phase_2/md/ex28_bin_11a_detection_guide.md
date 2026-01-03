# WAVファイル最大振幅検出の実装ガイド

## 目次
1. [はじめに：質問への回答](#はじめに質問への回答)
2. [WAVファイルのデータ構造の理解](#wavファイルのデータ構造の理解)
3. [サンプルデータの型選択](#サンプルデータの型選択)
4. [ビット深度ごとの符号処理](#ビット深度ごとの符号処理)
5. [実装手順](#実装手順)
6. [コード例と詳細解説](#コード例と詳細解説)
7. [テスト方法](#テスト方法)

---

## はじめに：質問への回答

### Q1: サンプルデータを格納する変数の型は何が適切ですか？

**A: `int`型（4バイト）を静的に使用するのが最適です。動的な型定義は必要ありません。**

#### 詳しい理由

**1. Cにおける動的型定義の制約**

C言語には、PythonやJavaScriptのような動的型付け機能がありません。変数の型は**コンパイル時**に決定される必要があります。

```c
// Cではこのような動的型定義はできません
if (bit_depth == 8) {
    uint8_t sample;  // ✗ スコープ外で使えない
} else if (bit_depth == 16) {
    int16_t sample;  // ✗ スコープ外で使えない
}
```

理論上可能なアプローチとその問題点：

| アプローチ | 実装方法 | 問題点 |
|----------|---------|-------|
| `void*`ポインタ | `void*`で汎用的に扱う | 型安全性が失われ、キャストが複雑化 |
| `union`型 | 複数の型を1つに統合 | 結局`switch`で分岐が必要 |
| マクロ展開 | プリプロセッサで型を切り替え | コンパイル時に決定され、実行時は不可 |

**2. 既存コードベースのパターン**

プロジェクト内の既存ファイルを調査したところ、すべてのファイルで**`int`型を汎用コンテナ**として使用していることが判明しました：

- [ex28_bin_10a.c:87](../ex28_bin_10a.c#L87)
  ```c
  int bin_data = 0;
  if (fread(&bin_data, bytes_per_sample, 1, fp) != 1) { ... }
  ```

- [ex28_bin_10b.c:95](../ex28_bin_10b.c#L95)
  ```c
  int bin_data = 0;
  fread(&bin_data, bytes_per_sample, 1, fp);
  ```

- [test_ex28_bin_10b.c:98](../test_ex28_bin_10b.c#L98)
  ```c
  int bin_data = 0;
  fread(&bin_data, bytes_per_sample, 1, fp);
  ```

このパターンには重要な利点があります：
- **一貫性**: コードベース全体で同じアプローチ
- **シンプル**: 型を意識せずに読み込める
- **実用的**: `int`は十分な容量を持つ

**3. `int`型の容量の十分性**

現代のほとんどのシステム（Linux、Windows、macOS）では、`int`は**4バイト（32ビット）**です。

```c
#include <stdio.h>
int main() {
    printf("sizeof(int) = %zu bytes\n", sizeof(int));
    // 出力: sizeof(int) = 4 bytes
}
```

これは、すべてのWAVサンプル形式を格納するのに十分です：

| ビット深度 | 必要バイト数 | `int`で格納可能？ |
|----------|------------|----------------|
| 8-bit    | 1バイト     | ✓（余裕あり） |
| 16-bit   | 2バイト     | ✓（余裕あり） |
| 24-bit   | 3バイト     | ✓（余裕あり） |
| 32-bit   | 4バイト     | ✓（ぴったり） |

**4. リトルエンディアンの仕組み**

WAVファイルは**リトルエンディアン**形式です。これは、バイトが「下位から上位」に格納される方式です。

```
例：16-bit サンプル値 0x1234 をメモリに格納

アドレス:  [0x00] [0x01] [0x02] [0x03]
リトル:      34     12     00     00
ビッグ:      00     00     12     34  （参考：WAVでは使われない）
```

`int`型（4バイト）に16-bitデータ（2バイト）を`fread`すると：

```c
int buffer = 0;  // 初期値: 0x00000000
fread(&buffer, 2, 1, fp);  // 2バイト読み込み

// 結果: buffer = 0x00001234
//       ↑上位2バイトは0のまま、下位2バイトに値が入る
```

これにより、**どのビット深度でも`int`で受け取れる**のです。

---

### Q2: block_alignに従った処理は必要ですか？

**A: はい、絶対に必要です。`block_align`単位で読み込まないとデータが壊れます。**

#### 詳しい理由

**1. block_alignとは何か**

`block_align`は「**1フレームのバイト数**」を示します。

```c
block_align = (bit_depth / 8) × channel_num
```

例：
```
16-bit ステレオ:
  bit_depth = 16
  channel_num = 2
  block_align = (16 / 8) × 2 = 2 × 2 = 4 バイト

24-bit モノラル:
  bit_depth = 24
  channel_num = 1
  block_align = (24 / 8) × 1 = 3 × 1 = 3 バイト
```

**2. フレームとは**

「フレーム」は**特定の時点における全チャンネルのサンプル**です。

```
ステレオ（2チャンネル）のフレーム構造:

時刻 t=0:  [左チャンネル][右チャンネル] ← これが1フレーム
時刻 t=1:  [左チャンネル][右チャンネル] ← これが1フレーム
時刻 t=2:  [左チャンネル][右チャンネル] ← これが1フレーム
```

ファイル内のデータ配置（インターリーブ）:
```
[L0][R0][L1][R1][L2][R2][L3][R3]...
 ←1フレーム→
      ←1フレーム→
           ←1フレーム→
```

**重要**: データは`[L0][L1][L2]...[R0][R1][R2]...`のようには並んでいません！

**3. なぜblock_align単位で読むべきか**

バイト単位で読むと、サンプルが分割されてしまいます：

```
16-bit ステレオ（block_align = 4）のデータ:
  [L0_下位][L0_上位][R0_下位][R0_上位][L1_下位][L1_上位]...
   ↑1バイト ↑1バイト ↑1バイト ↑1バイト

1バイトずつ読むと:
  1回目: L0_下位  ← 不完全なデータ
  2回目: L0_上位  ← L0が完成するが、Rがない
  3回目: R0_下位  ← 不完全なデータ
  ...

4バイトずつ読むと:
  1回目: [L0_下位][L0_上位][R0_下位][R0_上位] ← 完全な1フレーム ✓
  2回目: [L1_下位][L1_上位][R1_下位][R1_上位] ← 完全な1フレーム ✓
```

**4. 既存コードの検証**

[test_ex28_bin_10b.c:79](../test_ex28_bin_10b.c#L79)では、オフセットがblock_alignの倍数かどうかを明示的にチェックしています：

```c
long remainder = byte_offset % fmt->block_align;
if (remainder == 0) {
    fprintf(stderr, " ✓ (aligned)\n");
} else {
    fprintf(stderr, " ✗ (NOT aligned!)\n");
    fprintf(stderr, "WARNING: byte_offset is not aligned to block_align!\n");
}
```

これは、コードベースが**block_align境界を重視している**証拠です。

---

## WAVファイルのデータ構造の理解

### WAVファイルの全体構造

```
+------------------------+
| RIFFヘッダー (12 bytes) |
|  - "RIFF" (4 bytes)    |
|  - ファイルサイズ (4)   |
|  - "WAVE" (4 bytes)    |
+------------------------+
| fmtチャンク             |
|  - "fmt " (4 bytes)    |
|  - チャンクサイズ (4)   |
|  - オーディオ形式 (2)   |
|  - チャンネル数 (2)     |
|  - サンプルレート (4)   |
|  - バイトレート (4)     |
|  - block_align (2)     | ← 重要
|  - bit_depth (2)       | ← 重要
+------------------------+
| (その他のチャンク)      |
+------------------------+
| dataチャンク            |
|  - "data" (4 bytes)    |
|  - データサイズ (4)     |
|  - サンプルデータ       | ← ここを走査する
+------------------------+
```

### 現在のex28_bin_11a.cの進捗

現在のコード（159行目まで）は以下を実装済み：

1. ✓ RIFFヘッダーの読み込み（118行目）
2. ✓ WAVファイルの検証（123行目）
3. ✓ fmtチャンクの読み込み（`process_read`関数）
4. ✓ dataチャンクの検出と位置取得（`process_read`関数）
5. ✓ dataオフセットへのシーク（152行目）
6. **未実装**: サンプルデータの走査と最大振幅の検出 ← これから実装

---

## サンプルデータの型選択

### 推奨アプローチ：静的な`int`型コンテナ

```c
// 読み込み用のバッファ（すべてのbit_depthに対応）
int raw_buffer = 0;

// bytes_per_sampleは動的に計算
uint32_t bytes_per_sample = (fmt->bit_depth / 8) * fmt->channel_num;

// 実際の読み込み
fread(&raw_buffer, bytes_per_sample, 1, fp);
```

### なぜこのアプローチが優れているか

| 比較項目 | `int`静的アプローチ | 動的型アプローチ |
|---------|-------------------|----------------|
| コードの複雑さ | シンプル | 複雑（型判定分岐が必要） |
| 実行速度 | 高速 | 分岐により低下 |
| 保守性 | 高い（一箇所で処理） | 低い（各所で型チェック） |
| バグの可能性 | 低い | 高い（型ミスのリスク） |
| 既存コードとの一貫性 | ✓ | ✗ |

### 読み込みのメカニズム

```c
// 例：16-bit ステレオ（4バイト）を読み込む

int raw_buffer = 0;  // 初期状態: 0x00000000

fread(&raw_buffer, 4, 1, fp);
// ファイル内容: [0x12][0x34][0x56][0x78]
//                ↓
// raw_buffer = 0x78563412（リトルエンディアン）

// これを解釈すると：
// 左チャンネル = 0x3412（下位16ビット）
// 右チャンネル = 0x7856（上位16ビット）
```

---

## ビット深度ごとの符号処理

### 符号付き vs 符号なし

WAVフォーマットの仕様では、ビット深度によって符号の扱いが異なります：

| ビット深度 | 符号 | 値の範囲 | 中心値 |
|----------|------|---------|-------|
| 8-bit | **符号なし** | 0 ～ 255 | 128（無音） |
| 16-bit | **符号付き** | -32,768 ～ 32,767 | 0（無音） |
| 24-bit | **符号付き** | -8,388,608 ～ 8,388,607 | 0（無音） |
| 32-bit | **符号付き** | -2,147,483,648 ～ 2,147,483,647 | 0（無音） |

### なぜ8-bitだけ特別なのか

歴史的理由により、8-bit PCMは符号なし形式が標準となりました。

```
8-bit サンプル値の意味:
  0   = 最小振幅（負のピーク）
  128 = 無音（ゼロ振幅）
  255 = 最大振幅（正のピーク）

これを符号付き形式に変換:
  0   → -128
  128 → 0
  255 → +127

変換式: signed_value = unsigned_value - 128
```

### 符号拡張の必要性

24-bit サンプルは3バイトですが、Cには3バイト整数型がありません。そのため、4バイトの`int32_t`に変換する際、**符号拡張**が必要です。

#### 符号拡張とは

```
24-bit 値: 0x800000（負の値）
  ビット表現: 1000 0000 0000 0000 0000 0000
               ↑ ビット23が1 = 負の数

これを32-bitに拡張:
  間違った方法（ゼロ拡張）:
    0x00800000 = +8,388,608（正の大きな数になってしまう）

  正しい方法（符号拡張）:
    0xFF800000 = -8,388,608（負の数として維持）
    ↑ 上位8ビットを1で埋める
```

#### 符号拡張の実装

```c
// 24-bit サンプルの符号拡張
if (raw_buffer & 0x800000) {
    // ビット23が1 → 負の数
    // 上位8ビットを1で埋める
    sample = raw_buffer | 0xFF000000;
} else {
    // ビット23が0 → 正の数
    // 上位8ビットを0で埋める（実質そのまま）
    sample = raw_buffer & 0x00FFFFFF;
}
```

### 全ビット深度対応の変換関数

```c
int32_t extract_signed_sample(int raw_buffer, uint16_t bit_depth) {
    int32_t sample;

    switch (bit_depth) {
        case 8:
            // 符号なし → 符号付き変換
            sample = ((uint8_t)raw_buffer) - 128;
            break;

        case 16:
            // 既に符号付き、キャストのみ
            sample = (int16_t)raw_buffer;
            break;

        case 24:
            // 符号拡張が必要
            if (raw_buffer & 0x800000) {
                sample = raw_buffer | 0xFF000000;
            } else {
                sample = raw_buffer & 0x00FFFFFF;
            }
            break;

        case 32:
            // 既に符号付き、そのまま
            sample = raw_buffer;
            break;

        default:
            fprintf(stderr, "Unsupported bit_depth: %u\n", bit_depth);
            return 0;
    }

    return sample;
}
```

### 変換の動作例

#### 8-bit変換の例

```c
// ファイルから読んだ値: 200（符号なし）
uint8_t raw = 200;

// 符号付きに変換
int32_t sample = raw - 128;
// 結果: 200 - 128 = 72（正のピーク）

// 別の例: 50（符号なし）
raw = 50;
sample = raw - 128;
// 結果: 50 - 128 = -78（負のピーク）
```

#### 16-bit変換の例

```c
// ファイルから読んだ値（リトルエンディアン）
// バイト列: [0x00][0x80] → 0x8000

int raw_buffer = 0x8000;

// 符号付き16-bitとして解釈
int16_t sample = (int16_t)raw_buffer;
// 結果: -32768（最小値、負のピーク）

// 別の例: [0xFF][0x7F] → 0x7FFF
raw_buffer = 0x7FFF;
sample = (int16_t)raw_buffer;
// 結果: 32767（最大値、正のピーク）
```

#### 24-bit変換の例

```c
// 例1: 負の値
int raw_buffer = 0x800000;

if (raw_buffer & 0x800000) {  // ビット23が1
    int32_t sample = raw_buffer | 0xFF000000;
    // 結果: 0xFF800000 = -8,388,608
}

// 例2: 正の値
raw_buffer = 0x7FFFFF;

if (raw_buffer & 0x800000) {  // ビット23が0
    // この条件は偽
} else {
    int32_t sample = raw_buffer & 0x00FFFFFF;
    // 結果: 0x007FFFFF = 8,388,607
}
```

---

## 実装手順

### ステップ1: `extract_signed_sample`関数の追加

**場所**: [ex28_bin_11a.c:102](../ex28_bin_11a.c#L102)（`process_read`関数の後、`main`関数の前）

```c
// process_read関数の終わり（101行目）の後に追加

/**
 * 生のバッファデータを符号付きサンプル値に変換
 *
 * @param raw_buffer freadで読み込んだ生データ
 * @param bit_depth WAVファイルのビット深度（8, 16, 24, 32）
 * @return 符号付き32-bit整数としてのサンプル値
 */
int32_t extract_signed_sample(int raw_buffer, uint16_t bit_depth) {
    int32_t sample;

    switch (bit_depth) {
        case 8:
            // 8-bitは符号なし（0～255）→ 符号付き（-128～127）に変換
            sample = ((uint8_t)raw_buffer) - 128;
            break;

        case 16:
            // 16-bitは既に符号付き → キャストのみ
            sample = (int16_t)raw_buffer;
            break;

        case 24:
            // 24-bit → 32-bit符号拡張
            // ビット23（符号ビット）をチェック
            if (raw_buffer & 0x800000) {
                // 負の数：上位8ビットを1で埋める
                sample = raw_buffer | 0xFF000000;
            } else {
                // 正の数：上位8ビットを0で埋める
                sample = raw_buffer & 0x00FFFFFF;
            }
            break;

        case 32:
            // 32-bitは既に符号付き → そのまま使用
            sample = raw_buffer;
            break;

        default:
            fprintf(stderr, "ERROR extract_signed_sample: Unsupported bit_depth: %u\n", bit_depth);
            return 0;
    }

    return sample;
}
```

### ステップ2: `find_max_amplitude`関数の追加

**場所**: `extract_signed_sample`関数の後、`main`関数の前

```c
/**
 * WAVファイルのサンプルデータを走査し、最大振幅を検出
 *
 * @param fp ファイルポインタ
 * @param fmt fmtチャンク情報
 * @param data_size dataチャンクのサイズ（バイト）
 * @param data_offset dataチャンクの開始位置
 * @return 最大振幅値（エラー時は-1）
 */
int32_t find_max_amplitude(FILE *fp, const FmtChunk *fmt,
                          uint32_t data_size, long data_offset) {

    // データチャンクの先頭に移動
    if (fseek(fp, data_offset, SEEK_SET) != 0) {
        fprintf(stderr, "ERROR fseek/find_max_amplitude: Cannot seek to data_offset\n");
        return -1;
    }

    // パラメータ計算
    uint32_t bytes_per_sample = (fmt->bit_depth / 8) * fmt->channel_num;
    uint32_t bytes_per_channel = fmt->bit_depth / 8;
    uint32_t total_frames = data_size / bytes_per_sample;

    fprintf(stderr, "\n=== find_max_amplitude: Starting scan ===\n");
    fprintf(stderr, "Bit depth: %u bits\n", fmt->bit_depth);
    fprintf(stderr, "Channels: %u\n", fmt->channel_num);
    fprintf(stderr, "Bytes per sample: %u bytes\n", bytes_per_sample);
    fprintf(stderr, "Total frames: %u\n", total_frames);

    // 最大振幅を追跡
    int32_t max_amplitude = 0;
    long max_position = 0;

    // 全フレームを走査
    for (uint32_t frame = 0; frame < total_frames; frame++) {
        int raw_buffer = 0;

        // 1フレーム分のデータを読み込み
        if (fread(&raw_buffer, bytes_per_sample, 1, fp) != 1) {
            if (feof(fp)) {
                fprintf(stderr, "find_max_amplitude: Reached end of file at frame %u\n", frame);
                break;
            }
            fprintf(stderr, "ERROR fread/find_max_amplitude: Cannot read sample at frame %u\n", frame);
            return -1;
        }

        // フレーム内の各チャンネルを処理
        for (uint16_t ch = 0; ch < fmt->channel_num; ch++) {
            int channel_sample = 0;

            // このチャンネルのバイト列をraw_bufferから抽出
            memcpy(&channel_sample,
                   ((uint8_t*)&raw_buffer) + (ch * bytes_per_channel),
                   bytes_per_channel);

            // 符号付きサンプル値に変換
            int32_t signed_sample = extract_signed_sample(channel_sample, fmt->bit_depth);

            // 絶対値を計算（振幅）
            int32_t abs_amplitude;
            if (signed_sample == INT32_MIN) {
                // INT32_MIN（-2147483648）は符号反転できないため特別処理
                abs_amplitude = INT32_MAX;
            } else {
                abs_amplitude = (signed_sample < 0) ? -signed_sample : signed_sample;
            }

            // 最大値を更新
            if (abs_amplitude > max_amplitude) {
                max_amplitude = abs_amplitude;
                max_position = data_offset + (frame * bytes_per_sample) + (ch * bytes_per_channel);
            }
        }
    }

    fprintf(stderr, "find_max_amplitude: Scan completed\n");
    fprintf(stderr, "Maximum amplitude: %d\n", max_amplitude);
    fprintf(stderr, "Position in file: %ld bytes\n", max_position);

    return max_amplitude;
}
```

### ステップ3: `main`関数での呼び出し

**場所**: [ex28_bin_11a.c:156](../ex28_bin_11a.c#L156)の後

現在のコードは156行目でdataオフセットにシークした後、何もせず終了しています。ここに最大振幅検出のコードを追加します：

```c
    // 既存のコード（152～156行目）
    if (fseek(fp, data_offset, SEEK_SET) != 0) {
        fprintf(stderr, "ERROR fread/main: Cannot move to data_offset\n");
        fprintf(stderr, "data_offset: %ld\n", data_offset);
        return -1;
    }

    // ここから追加 ↓

    // 最大振幅を検出
    int32_t max_amplitude = find_max_amplitude(fp, &fmt, data_size, data_offset);
    if (max_amplitude == -1) {
        fprintf(stderr, "ERROR find_max_amplitude/main: Function returned error\n");
        fclose(fp);
        return -1;
    }

    // 結果を表示
    printf("\n");
    printf("=================================\n");
    printf("  Maximum Amplitude Detection   \n");
    printf("=================================\n");
    printf("File: %s\n", file_name);
    printf("Bit depth: %u bits\n", fmt.bit_depth);
    printf("Channels: %u\n", fmt.channel_num);
    printf("Sample rate: %u Hz\n", fmt.sample_rate);
    printf("---------------------------------\n");
    printf("Maximum amplitude: %d\n", max_amplitude);
    printf("=================================\n");
    printf("\n");

    // ファイルを閉じて終了
    fclose(fp);
    return 0;
}
```

---

## コード例と詳細解説

### マルチチャンネルのサンプル抽出

最も複雑な部分は、マルチチャンネルデータから各チャンネルを抽出する処理です。

#### メモリレイアウトの理解

16-bit ステレオの場合：

```
メモリ上のデータ配置（1フレーム = 4バイト）:

アドレス:    [0x00] [0x01] [0x02] [0x03]
意味:        L_下位  L_上位  R_下位  R_上位
バイト値:      0x12   0x34   0x56   0x78

int型で読むと（リトルエンディアン）:
raw_buffer = 0x78563412
             ↑   ↑   ↑   ↑
             |   |   |   +--- 最下位バイト（アドレス0x00）
             |   |   +------- 2番目のバイト（アドレス0x01）
             |   +----------- 3番目のバイト（アドレス0x02）
             +--------------- 最上位バイト（アドレス0x03）
```

#### チャンネル抽出のコード

```c
// 例：16-bit ステレオ（channel_num = 2）

uint32_t bytes_per_channel = fmt->bit_depth / 8;  // = 16 / 8 = 2

for (uint16_t ch = 0; ch < fmt->channel_num; ch++) {
    int channel_sample = 0;

    // チャンネル0（左）の場合:
    //   オフセット = 0 * 2 = 0
    //   &raw_buffer + 0 から2バイトコピー
    //   → 0x3412をコピー

    // チャンネル1（右）の場合:
    //   オフセット = 1 * 2 = 2
    //   &raw_buffer + 2 から2バイトコピー
    //   → 0x7856をコピー

    memcpy(&channel_sample,
           ((uint8_t*)&raw_buffer) + (ch * bytes_per_channel),
           bytes_per_channel);

    // これでchannel_sampleには個別チャンネルの値が入る
}
```

#### `memcpy`の詳細

```c
// memcpyのシグネチャ
void *memcpy(void *dest, const void *src, size_t n);

// 使用例の分解
memcpy(
    &channel_sample,                                   // コピー先
    ((uint8_t*)&raw_buffer) + (ch * bytes_per_channel), // コピー元
    bytes_per_channel                                  // バイト数
);
```

**コピー元の計算過程**:

```c
// raw_bufferのアドレスを取得
&raw_buffer  // 例: 0x1000

// uint8_t*（1バイト単位のポインタ）にキャスト
(uint8_t*)&raw_buffer  // 0x1000（型が変わっただけ）

// チャンネルごとのオフセットを加算
// ch=0: 0x1000 + (0 * 2) = 0x1000（左チャンネルの先頭）
// ch=1: 0x1000 + (1 * 2) = 0x1002（右チャンネルの先頭）
((uint8_t*)&raw_buffer) + (ch * bytes_per_channel)
```

### 振幅の絶対値計算

振幅は「音の大きさ」を表すため、正負に関係なく絶対値で評価します。

```c
int32_t signed_sample = -15000;  // 負のピーク

// 絶対値を計算
int32_t abs_amplitude;
if (signed_sample < 0) {
    abs_amplitude = -signed_sample;  // -(-15000) = 15000
} else {
    abs_amplitude = signed_sample;
}

// 別の例：正のピーク
signed_sample = 12000;
abs_amplitude = (signed_sample < 0) ? -signed_sample : signed_sample;
// 結果: 12000

// 比較: 15000 > 12000 なので、負のピークの方が振幅が大きい
```

### INT32_MIN問題への対処

32-bit符号付き整数には特殊な値があります：

```c
#include <stdint.h>

INT32_MIN = -2,147,483,648  // 最小値
INT32_MAX = +2,147,483,647  // 最大値

// 問題：INT32_MINの絶対値はINT32_MAXを超える
abs(INT32_MIN) = 2,147,483,648  // これは表現できない！

// Cでの実際の動作（未定義動作）
int32_t value = INT32_MIN;
int32_t result = -value;  // オーバーフロー → 結果は不定

// 正しい対処法
if (signed_sample == INT32_MIN) {
    abs_amplitude = INT32_MAX;  // 最大値で代用
} else {
    abs_amplitude = (signed_sample < 0) ? -signed_sample : signed_sample;
}
```

---

## テスト方法

### テストファイルの準備

以下のようなテストファイルを用意すると良いでしょう：

| ファイル名 | ビット深度 | チャンネル | 特徴 |
|----------|----------|----------|-----|
| test_16bit_stereo.wav | 16-bit | 2（ステレオ） | 最も一般的な形式 |
| test_8bit_mono.wav | 8-bit | 1（モノラル） | 符号なし変換のテスト |
| test_24bit_stereo.wav | 24-bit | 2（ステレオ） | 符号拡張のテスト |
| test_32bit_mono.wav | 32-bit | 1（モノラル） | オーバーフロー対策のテスト |

### コンパイルとテスト実行

```bash
# コンパイル
gcc -o ex28_bin_11a ex28_bin_11a.c -Wall -Wextra

# 実行
./ex28_bin_11a test_16bit_stereo.wav
```

### 期待される出力

```
main: This file is WAV

process_read: fmt chunk detected
chunk_id: fmt
process_read: FmtChunk is loaded

process_read: data chunk detected
data_size: 176400
data_offset: 44

=== find_max_amplitude: Starting scan ===
Bit depth: 16 bits
Channels: 2
Bytes per sample: 4 bytes
Total frames: 44100
find_max_amplitude: Scan completed
Maximum amplitude: 32767
Position in file: 12345 bytes

=================================
  Maximum Amplitude Detection
=================================
File: test_16bit_stereo.wav
Bit depth: 16 bits
Channels: 2
Sample rate: 44100 Hz
---------------------------------
Maximum amplitude: 32767
=================================
```

### 検証ポイント

1. **Maximum amplitude値の妥当性**
   - 16-bit: 最大32767
   - 24-bit: 最大8388607
   - 32-bit: 最大2147483647

2. **Total framesの計算**
   ```c
   total_frames = data_size / bytes_per_sample

   // 例：16-bit ステレオ、1秒間の音声
   data_size = 44100 samples/sec * 4 bytes/sample = 176400 bytes
   bytes_per_sample = 4
   total_frames = 176400 / 4 = 44100 ← 1秒分 ✓
   ```

3. **既存ツールとの比較**
   ```bash
   # SoX（Sound eXchange）を使った検証
   sox test.wav -n stats

   # 出力例:
   # Maximum amplitude: 0.999969  （-32767/32768の正規化値）
   # → 実際の値: 32767 ✓
   ```

### デバッグ用の追加出力

開発中は、以下のようなデバッグ出力を追加すると問題の特定が容易になります：

```c
// find_max_amplitude関数内に追加

// 最初の10フレームを詳細表示
if (frame < 10) {
    fprintf(stderr, "Frame %u:\n", frame);
    for (uint16_t ch = 0; ch < fmt->channel_num; ch++) {
        int channel_sample = 0;
        memcpy(&channel_sample,
               ((uint8_t*)&raw_buffer) + (ch * bytes_per_channel),
               bytes_per_channel);

        int32_t signed_sample = extract_signed_sample(channel_sample, fmt->bit_depth);

        fprintf(stderr, "  Ch%u: raw=0x%08X, signed=%d\n",
                ch, channel_sample, signed_sample);
    }
}
```

---

## まとめ

### 重要なポイントの再確認

1. **型の選択**
   - `int`型（4バイト）を静的に使用
   - 動的型定義は不要かつ非現実的

2. **block_alignの重要性**
   - 必ず`block_align`単位で読み込む
   - `block_align = (bit_depth / 8) * channel_num`

3. **符号処理**
   - 8-bitのみ符号なし（変換必要）
   - 24-bitは符号拡張が必要
   - 16-bitと32-bitはキャストのみ

4. **振幅の定義**
   - 絶対値で評価
   - 全チャンネル統合で最大値を検索

5. **エッジケース**
   - INT32_MINの特別処理
   - EOF検出
   - 部分的なフレームの処理

### コードの構造

```
ex28_bin_11a.c
├── ヘッダー・構造体定義（1～42行目）
├── process_read関数（44～101行目）
├── extract_signed_sample関数（新規追加）
├── find_max_amplitude関数（新規追加）
└── main関数（103～159行目 + 追加コード）
```

### 次のステップ

このガイドに従って実装した後、以下を検討してください：

1. **機能拡張**
   - チャンネル別の最大振幅表示
   - 最大振幅の時刻表示
   - RMS（二乗平均平方根）の計算

2. **エラー処理の強化**
   - 不正なWAVファイルの検出
   - サポート外フォーマットの警告

3. **パフォーマンス最適化**
   - バッファリングの改善
   - 大規模ファイルへの対応

---

## 参考資料

### WAVフォーマット仕様
- Microsoft WAVE PCM soundfile format
- http://soundfile.sapp.org/doc/WaveFormat/

### C言語の整数型
- `stdint.h`の型定義（`int8_t`, `int16_t`, `int32_t`など）
- エンディアンの理解

### 既存コードの参照先
- [ex28_bin_10b.c](../ex28_bin_10b.c): `int`バッファ読み込みパターン
- [test_ex28_bin_10b.c](../test_ex28_bin_10b.c): チャンネル分離の例
- [ex28_bin_10c.c](../ex28_bin_10c.c): バイト単位走査のループ構造
