# WAVファイル読み取りプログラム ex28_bin_10b の精査結果と修正提案

## 実行結果とデバッグ情報

```bash
NK-PC% $C_FILE/ex28_bin_10b_file $BIN_FILE/sample.wav 0.2
Sample data offset: 44
bytes_rate formula is correct
byte_offset(17640) = byte_rate(88200.00) * need_second(0.20)
result_offset(17684) = data_offset(44) + byte_offset(17640)
=== Result ===
bin: 0
```

## ✅ 重要な発見: コードは正しく動作している！

### 1. offset計算は完璧 ✅
```
byte_rate = 88200 バイト/秒
  = 44100 Hz × 2 バイト/サンプル (16bit)

0.2秒 × 88200 = 17640 バイト

ファイル位置 = data_offset(44) + byte_offset(17640) = 17684
```

計算は数学的に100%正しいです。

### 2. freadは成功している ✅
- エラーメッセージが出ていない
- つまり、ファイルから4バイト正常に読み取れている
- `bytes_per_sample = 4` (16bit × 2ch ÷ 8)

### 3. bin: 0 が表示される理由

**結論: その位置のサンプルデータが実際に 0x00000000 (無音) の可能性が高い**

WAVファイルの最初の0.2秒が無音区間、またはその位置が静寂部分である可能性があります。

## 🔍 検証方法

### 方法1: 別の秒数で試す（最も簡単）

```bash
# 異なる位置で試す
$C_FILE/ex28_bin_10b_file $BIN_FILE/sample.wav 0.5
$C_FILE/ex28_bin_10b_file $BIN_FILE/sample.wav 1.0
$C_FILE/ex28_bin_10b_file $BIN_FILE/sample.wav 0.0
```

もし他の秒数で0以外の値が出れば、コードは完全に正しく動作しています。

### 方法2: デバッグコードを追加して16進数で確認

`get_bin` 関数の96行目（freadの後）に以下を追加：

```c
// freadの後に追加
fprintf(stderr, "Debug: bin_data = 0x%08X (hex) = %d (dec)\n",
        (unsigned int)bin_data, bin_data);
fprintf(stderr, "Debug: bytes_per_sample = %u\n", bytes_per_sample);

// 16bitステレオの場合、左右チャネルに分解して表示
if (bytes_per_sample == 4 && fmt->bit_depth == 16) {
    int16_t left = (int16_t)(bin_data & 0xFFFF);
    int16_t right = (int16_t)((bin_data >> 16) & 0xFFFF);
    fprintf(stderr, "Debug: Left channel = %d, Right channel = %d\n", left, right);
}
```

**これにより**:
- 実際に読み取ったバイナリ値を16進数で確認できる
- 左右チャネルごとの値が分かる

### 方法3: xxd コマンドでファイルを直接確認

```bash
# 17684バイト目から16バイト分を16進数表示
xxd -s 17684 -l 16 $BIN_FILE/sample.wav
```

ファイルの実際の内容を直接確認できます。

## 🔴 発見済みのバグ（副次的な問題）

### バグ1: エラーハンドリングの改善が必要（92, 98行目）

現在のコード:
```c
if (fseek(fp, result_offset, SEEK_SET) != 0) {
    fprintf(stderr, "fseek/get_bin: returned error\n");
    return 1;  // ← エラーなのに1を返している
}

if (fread(&bin_data, bytes_per_sample, 1, fp) != 1) {
    fprintf(stderr, "fread/get_bin: returned error\n");
    return 1;  // ← エラーなのに1を返している
}
```

問題点:
- エラー時に `return 1` を返している
- しかし、正常時に読み取ったデータが偶然1だったら区別できない
- 66行目のコメントで「error時の戻り値は、必ず負の数にしないと」と書いているのに実装が違う

修正案:
```c
if (fseek(fp, result_offset, SEEK_SET) != 0) {
    fprintf(stderr, "fseek/get_bin: returned error\n");
    return -1;  // 統一して-1にする
}

if (fread(&bin_data, bytes_per_sample, 1, fp) != 1) {
    fprintf(stderr, "fread/get_bin: returned error\n");
    return -1;  // 統一して-1にする
}
```

### バグ2: main関数のエラーチェック（182行目）

現在は修正済み:
```c
if (bin_data == -1) {  // ✅ これは正しい
```

しかし、上記のバグ1が残っているため、fseekやfreadのエラーは検出できません。

## 📋 WAVフォーマットの理解

### 16bit ステレオWAVの構造

```
[ヘッダー: 44バイト]
[L0][R0][L1][R1][L2][R2]...
 └─ 4バイト ─┘
    (1フレーム)
```

- 1サンプル値 = 2バイト (16bit)
- 1フレーム = 4バイト (左2バイト + 右2バイト)
- リトルエンディアンで格納

### 現在のコードの動作

```c
uint32_t bits_per_sample = fmt->bit_depth * fmt->channel_num;  // 16 × 2 = 32
uint32_t bytes_per_sample = bits_per_sample / 8;                // 4
```

これは**1フレーム全体**のバイト数を計算しています（正しい）。

```c
int bin_data = 0;
fread(&bin_data, 4, 1, fp);  // 4バイト = 1フレーム読み取り
```

`int bin_data` (4バイト) に:
- 下位16bit: 左チャネル
- 上位16bit: 右チャネル

が格納されます。

## 🎯 推奨される修正手順

### ステップ1: 動作確認（最優先）

まず別の秒数で試して、コードが正しく動作しているか確認:
```bash
$C_FILE/ex28_bin_10b_file $BIN_FILE/sample.wav 0.5
```

### ステップ2: デバッグ出力追加

上記「方法2」のデバッグコードを追加して、実際の値を確認

### ステップ3: エラーハンドリングの統一

92行目と98行目の `return 1` を `return -1` に修正

### ステップ4: （オプション）出力形式の改善

main関数の出力を改善:
```c
printf("=== Result ===\n");
printf("bin_data (raw): 0x%08X\n", (unsigned int)bin_data);
printf("bin_data (dec): %d\n", bin_data);

// 16bitステレオの場合は左右に分解
if (/* 16bit stereo の条件 */) {
    int16_t left = (int16_t)(bin_data & 0xFFFF);
    int16_t right = (int16_t)((bin_data >> 16) & 0xFFFF);
    printf("Left channel:  %d\n", left);
    printf("Right channel: %d\n", right);
}
```

## 修正対象ファイル

- [ex28_bin_10b.c](../ex28_bin_10b.c)
  - **92行目**: `return 1` → `return -1`
  - **98行目**: `return 1` → `return -1`
  - **96-100行目付近**: デバッグ出力を追加（方法2）
  - **187-189行目**: （オプション）出力形式の改善

## 期待される結果

- 別の秒数で試すと、0以外の値が読み取れることを確認
- デバッグ出力で実際のバイナリ値が確認できる
- エラーハンドリングが統一され、バグが減る
- 左右チャネルごとの値が分かる

## 学習ポイント

1. **デバッグは段階的に**: まず計算が正しいか確認→次にデータが正しいか確認
2. **型の選択**: 整数計算には `uint32_t`、ファイル位置には `long`、時間計算には `float`
3. **エラー値とデータ値は分離**: 同じ型で返すと混同する（今回のバグ）
4. **16進数表示は重要**: バイナリデータは16進数で見ると理解しやすい
5. **実際のデータを確認**: 想定と実際のデータが異なることは多い
