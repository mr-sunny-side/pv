# ex28_bin_5.c - Valgrind出力解析とコードレビュー

## 実行日
2025-12-23

## 問題の概要
プログラム実行時にスタック（動作が停止）し、Ctrl+Cで中断せざるを得ない状況が発生しました。

---

## Valgrind出力の重要なポイント

### 1. プログラムの停止箇所
```
==18621== Process terminating with default action of signal 2 (SIGINT)
==18621==    at 0x497D5A2: write (write.c:26)
==18621==    by 0x48F4974: _IO_file_write@@GLIBC_2.2.5 (fileops.c:1181)
==18621==    by 0x48F3570: new_do_write (fileops.c:449)
==18621==    by 0x48F4AAE: _IO_new_file_xsputn (fileops.c:1244)
==18621==    by 0x48E7A11: fwrite (iofwrite.c:39)
==18621==    by 0x10972D: main
```

**解釈**: プログラムは`fwrite()`の呼び出し中に無限ループまたは大量のデータ書き込みを行っている状態でスタックしています。

### 2. メモリリーク情報
```
==18621== HEAP SUMMARY:
==18621==     in use at exit: 9,136 bytes in 4 blocks
==18621==   total heap usage: 4 allocs, 0 frees, 9,136 bytes allocated
```

**解釈**:
- `0 frees` = プログラムが正常終了していないため、`fclose()`が呼ばれていない
- `still reachable: 9,136 bytes` = メモリリークではなく、FILE構造体のバッファが残っている
- エラーカウント0 = メモリアクセス違反はない（ロジックの問題）

---

## コードの問題点

### 🔴 致命的: BMPヘッダーを出力ファイルに書き込んでいない

**場所**: 112-121行目

```c
FILE *out_fp = fopen(output, "wb");
if (out_fp == NULL) {
    fprintf(stderr, "Cannot open %s\n", output);
    return 1;
}

int result = 0;
int x = 0;
int y = 0;
for (y = ih.height - 1; y >= 0; y--) {  // ← すぐにピクセルループ開始
```

**問題**:
- 出力ファイルを開いた直後、ヘッダー（`BmpFileHeader`と`BmpInfoHeader`）を書き込まずにピクセルデータの書き込みを開始している
- BMPファイルフォーマットでは、ファイルの先頭にヘッダー情報が必須

**BMPファイルの構造**:
```
[BmpFileHeader (14 bytes)]
[BmpInfoHeader (40+ bytes)]
[ピクセルデータ（各行はパディング含む）]
```

**修正方法**:
```c
FILE *out_fp = fopen(output, "wb");
if (out_fp == NULL) {
    fprintf(stderr, "Cannot open %s\n", output);
    return 1;
}

// ヘッダーを書き込む
if (fwrite(&fh, sizeof(fh), 1, out_fp) != 1) {
    fprintf(stderr, "Failed to write file header\n");
    fclose(fp);
    fclose(out_fp);
    return 1;
}

if (fwrite(&ih, sizeof(ih), 1, out_fp) != 1) {
    fprintf(stderr, "Failed to write info header\n");
    fclose(fp);
    fclose(out_fp);
    return 1;
}

// その後ピクセルデータを書き込む
for (y = ih.height - 1; y >= 0; y--) {
    // ...
}
```

---

### 🟡 重要: グレースケール計算の誤り

**場所**: 63-72行目

```c
void turn_to_gray(Pixel *px) {
    px->red *= 0.299;    // ❌ 間違い
    px->green *= 0.587;
    px->blue *= 0.114;
}
```

**問題**:
1. 各色成分を個別に係数で掛けているだけで、合算していない
2. 元の値が`uint8_t`（0-255）なので、小数を掛けると値が小さくなるだけ
3. グレースケールは「すべてのRGB値を同じ輝度値にする」必要がある

**例**:
- 入力: R=100, G=150, B=50
- 現在の計算: R=29.9, G=88.05, B=5.7 → uint8_tにキャスト → R=29, G=88, B=5
- これはグレースケールではなく、暗い色のRGB

**正しい計算**:
```c
void turn_to_gray(Pixel *px) {
    // 輝度を計算（人間の目の感度に基づく加重平均）
    uint8_t gray = (uint8_t)(px->red * 0.299 + px->green * 0.587 + px->blue * 0.114);

    // すべての色成分を同じ値にする
    px->red = gray;
    px->green = gray;
    px->blue = gray;
}
```

**結果**:
- 入力: R=100, G=150, B=50
- 正しい計算: gray = 100×0.299 + 150×0.587 + 50×0.114 = 124
- 出力: R=124, G=124, B=124（グレー）

---

### 🟡 重要: パディング計算の誤り

**場所**: 42行目

```c
int padding = 4 - (bytes_per_line % 4);  // ❌ 問題あり
```

**問題**:
- `bytes_per_line % 4`が0の場合（行が既に4バイト境界）、padding=4になる
- 実際には padding=0 であるべき

**例**:
- `bytes_per_line = 12` の場合
  - `12 % 4 = 0`
  - `padding = 4 - 0 = 4` ❌（不要なパディング）
- `bytes_per_line = 13` の場合
  - `13 % 4 = 1`
  - `padding = 4 - 1 = 3` ✓（正しい）

**修正方法**:
```c
int padding = (4 - (bytes_per_line % 4)) % 4;
```

または：
```c
int padding = (bytes_per_line % 4 == 0) ? 0 : (4 - (bytes_per_line % 4));
```

---

### 🟡 重要: 出力時のパディングが欠落

**場所**: 121-137行目（ピクセル書き込みループ）

```c
for (y = ih.height - 1; y >= 0; y--) {
    for (x = 0; x < ih.width; x++) {
        if ((result = get_pixels(fp, &fh, &ih, x, y, &px)) != 0) {
            // ...
        }
        turn_to_gray(&px);
        if (fwrite(&px, sizeof(px), 1, out_fp) != 1) {
            // ...
        }
    }
    // ← ここでパディングを書き込むべき
}
```

**問題**:
- BMPファイルでは各行のデータが4バイト境界にアラインされている必要がある
- 入力ファイルから読み取る際は`get_pixels()`で正しくオフセット計算している
- しかし出力時にはパディングを書き込んでいない

**修正方法**:
```c
int bytes_per_pixel = ih.bit_depth / 8;
int bytes_per_line = ih.width * bytes_per_pixel;
int padding = (4 - (bytes_per_line % 4)) % 4;
uint8_t padding_bytes[3] = {0, 0, 0};

for (y = ih.height - 1; y >= 0; y--) {
    for (x = 0; x < ih.width; x++) {
        if ((result = get_pixels(fp, &fh, &ih, x, y, &px)) != 0) {
            fprintf(stderr, "get_pixels returned error\n");
            fclose(fp);
            fclose(out_fp);
            return result;
        }
        turn_to_gray(&px);
        if (fwrite(&px, sizeof(px), 1, out_fp) != 1) {
            fprintf(stderr, "fwrite/main returned error\n");
            fclose(fp);
            fclose(out_fp);
            return 1;
        }
    }

    // 各行の終わりにパディングを書き込む
    if (padding > 0) {
        if (fwrite(padding_bytes, 1, padding, out_fp) != padding) {
            fprintf(stderr, "Failed to write padding\n");
            fclose(fp);
            fclose(out_fp);
            return 1;
        }
    }
}
```

---

### 🟢 小さな問題: pixel_offsetのデータ型

**場所**: 12行目

```c
typedef struct {
    uint16_t file_type;
    uint32_t file_size;
    uint16_t reserved_1;
    uint16_t reserved_2;
    uint16_t pixel_offset;  // ❌ uint16_t
} BmpFileHeader;
```

**問題**:
- BMPファイルヘッダーでは`pixel_offset`は`uint32_t`（4バイト）
- `uint16_t`（2バイト）を使うと構造体のサイズが間違う

**正しい定義**:
```c
typedef struct {
    uint16_t file_type;      // 2 bytes
    uint32_t file_size;      // 4 bytes
    uint16_t reserved_1;     // 2 bytes
    uint16_t reserved_2;     // 2 bytes
    uint32_t pixel_offset;   // 4 bytes ← 修正
} BmpFileHeader;              // 合計14バイト
```

---

## Valgrindから学べること

### 1. スタックトレースの読み方
```
at 0x497D5A2: write (write.c:26)
by 0x48F4974: _IO_file_write@@GLIBC_2.2.5 (fileops.c:1181)
by 0x48E7A11: fwrite (iofwrite.c:39)
by 0x10972D: main
```

- 下から上に読む: `main → fwrite → _IO_file_write → write`
- 一番上が実際に停止している関数
- `write`システムコールで止まっている = I/O操作中

### 2. メモリリークの種類
- **definitely lost**: 確実にリーク（アクセス不可能なメモリ）
- **indirectly lost**: 間接的にリーク
- **possibly lost**: リークの可能性
- **still reachable**: プログラム終了時点でアクセス可能（今回のケース）

### 3. エラーカウント
```
==18621== ERROR SUMMARY: 0 errors from 0 contexts
```

- メモリアクセス違反はない
- セグメンテーションフォルトではない
- → ロジックの問題（無限ループや誤った計算）

---

## 修正優先順位

1. **最優先**: BMPヘッダーの書き込み（これがないと正しいファイルにならない）
2. **高**: グレースケール計算の修正（現在の実装は間違っている）
3. **高**: パディング計算の修正
4. **高**: 出力時のパディング追加
5. **低**: pixel_offsetのデータ型（読み取りには影響しないが、正確性のため）

---

## 学習ポイント

### バイナリファイルフォーマットの重要性
- ヘッダーを含むすべての構造を正確に再現する必要がある
- 読み取りと書き込みで同じルールを適用する

### デバッグツールの活用
- Valgrindはメモリ問題だけでなく、スタックトレースも提供
- エラーカウントが0でも、ロジックの問題を示唆することがある

### グレースケール変換の理解
- 単純な掛け算ではなく、加重平均を計算する
- すべてのRGB成分を同じ値にする必要がある

### BMPファイルのパディング
- 各行は4バイト境界にアラインされる
- 読み取り時も書き込み時も考慮する必要がある

---

## 推奨される次のステップ

1. 上記の修正を1つずつ実装
2. 各修正後にコンパイルして動作確認
3. Valgrindで再度実行し、エラーがないことを確認
4. 出力されたBMPファイルを画像ビューアで開いて視覚的に確認
5. 元のファイルと出力ファイルのサイズを比較（同じであるべき）

---

## 参考: 完全な修正版の骨格

```c
// ヘッダー書き込み
fwrite(&fh, sizeof(fh), 1, out_fp);
fwrite(&ih, sizeof(ih), 1, out_fp);

// パディング計算
int bytes_per_pixel = ih.bit_depth / 8;
int bytes_per_line = ih.width * bytes_per_pixel;
int padding = (4 - (bytes_per_line % 4)) % 4;
uint8_t padding_bytes[3] = {0, 0, 0};

// ピクセル書き込み
for (y = ih.height - 1; y >= 0; y--) {
    for (x = 0; x < ih.width; x++) {
        get_pixels(fp, &fh, &ih, x, y, &px);
        turn_to_gray(&px);  // 修正版
        fwrite(&px, sizeof(px), 1, out_fp);
    }
    // 行ごとのパディング
    if (padding > 0) {
        fwrite(padding_bytes, 1, padding, out_fp);
    }
}
```

---

## まとめ

今回のスタック問題の根本原因は**BMPヘッダーの書き込み漏れ**でした。Valgrindは直接的なメモリエラーを検出しませんでしたが、スタックトレースから`fwrite`での停止を特定できました。

バイナリファイル処理では：
- ファイルフォーマットの完全な理解が必要
- 読み取りと書き込みの対称性を保つ
- デバッグツールを活用して問題箇所を特定

これらを意識することで、より堅牢なコードを書けるようになります。
