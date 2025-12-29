# WAVファイル読み取りプログラムの修正プラン

## 問題の概要
- コマンドライン引数で指定した秒数（小数可）の位置から、バイナリデータを読み取るプログラム
- 現在、1秒以下のファイルで小数点秒数を指定すると、offsetの計算が正しく動作しない
- 主な問題点：79行目の`result_offset`計算と、その他の関連する問題

## 修正が必要な箇所

### 1. 176行目：`atoi` → `atof` に変更
**現在の問題**:
```c
float need_second = atoi(argv[2]);  // 0.5 → 0 になってしまう
```

**修正後**:
```c
float need_second = atof(argv[2]);  // 0.5 → 0.5 として正しく読み取る
```

### 2. 79行目：offset計算の修正
**現在の問題**:
```c
int result_offset = data_offset + (bit_per_second / 8) * need_second;
// 右辺がfloat計算なのに、intにキャストされて精度が失われる
```

**修正後**:
```c
long result_offset = data_offset + (long)((bit_per_second / 8) * need_second);
// まずfloatで計算してから、longにキャストしてdata_offsetに加算
```

**計算の説明**:
- `bit_per_second / 8` = 1秒あたりのバイト数（byte_rate）
- `(bit_per_second / 8) * need_second` = 指定秒数までのバイト数
- これを`long`でキャストしてoffsetに加算

### 3. 82-89行目：読み取り処理の修正
**現在の問題**:
- `duration <= 1` の条件でのみ処理（1秒以上のファイルで動作しない）
- 読み取りバイト数の計算が複雑で不正確（`/ 10`の意図が不明確）

**修正後**:
```c
// bit_per_sampleはビット数なので、バイト数に変換
int read_bytes = (int)(bit_per_sample / 8);  // 1サンプル分のバイト数

if (fread(&bin_data, read_bytes, 1, fp) != 1) {
    fprintf(stderr, "fread/get_bin: Cannot read bin data\n");
    return 1;
}
```

**計算の説明**:
- `bit_per_sample` = bit_depth × channel_num（1サンプルのビット数）
- `bit_per_sample / 8` = 1サンプルのバイト数
- 例：16bit ステレオ → 16 × 2 = 32bit = 4バイト

### 4. 84-89行目の条件分岐を削除
- `duration <= 1` の条件は不要
- 全ての場合で同じ読み取り処理を行う

## 修正対象ファイル
- [ex28_bin_10b.c](../ex28_bin_10b.c)
  - 79行目：offset計算の型と計算順序を修正
  - 82-89行目：読み取りバイト数の計算を簡潔化
  - 84行目：`duration <= 1` の条件を削除
  - 176行目：`atoi` → `atof` に変更

## 期待される結果
- 0.5秒などの小数点秒数を指定しても正しく動作する
- 1秒以下のファイルでも1秒以上のファイルでも同じ処理で動作する
- 指定秒数の位置から正確に1サンプル分のデータを読み取れる
