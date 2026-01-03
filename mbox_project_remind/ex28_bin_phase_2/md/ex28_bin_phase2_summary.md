# ex28_bin Phase 2 総集編 (~10a) - WAVファイル解析で学ぶ本質的な落とし穴

## はじめに

このドキュメントは、WAVファイル解析演習(ex28_bin_8a~10a)で遭遇した主要なバグを総括し、**本質的な問題と頻繁に起こるミス**を抽出したものです。

### 対象演習
- ex28_bin_8e: Duration計算エラー
- ex28_bin_9b: 無限ループと複合的なバグ (Python)
- ex28_bin_10a: 型エラーと論理エラー (C言語)

---

## 第1部: WAVファイル解析の本質的な問題

### 1.1 未知チャンクのスキップ忘れ - 最頻出バグ

**問題**: WAVファイルには様々なチャンクが含まれるが、知らないチャンクをスキップしないと、後続のデータを正しく読めない。

#### 間違った実装
```c
int process_read(FILE *fp, FmtChunk *fmt, TmpChunk *tmp, ...) {
    if (fread(tmp, sizeof(*tmp), 1, fp) != 1) {
        return 1;
    }

    if (memcmp(tmp->chunk_id, "fmt ", 4) == 0) {
        // fmt処理
    }

    if (memcmp(tmp->chunk_id, "data", 4) == 0) {
        *data_size = tmp->chunk_size;
    }

    // ← 未知チャンク(JUNK, LIST)をスキップする処理がない！
    return 0;
}
```

**結果**: JUNKチャンクのヘッダを読んだ後、データ部分（143バイト）をスキップせずに次のfreadを実行すると、チャンクデータの途中から読み込んでしまう。

#### 正しい実装
```c
int process_read(FILE *fp, FmtChunk *fmt, TmpChunk *tmp, ...) {
    if (fread(tmp, sizeof(*tmp), 1, fp) != 1) {
        return 1;
    }

    if (memcmp(tmp->chunk_id, "fmt ", 4) == 0) {
        // fmt処理
    } else if (memcmp(tmp->chunk_id, "data", 4) == 0) {
        *data_size = tmp->chunk_size;
    } else {
        // 未知のチャンクをスキップ（必須！）
        fseek(fp, tmp->chunk_size, SEEK_CUR);
    }

    return 0;
}
```

**教訓**:
- チャンク解析では**必ず未知チャンクをスキップ**する処理を入れる
- `if-else if-else`構造で排他的に処理

---

### 1.2 fmtチャンクのサイズ計算ミス

**問題**: `chunk_size`に含まれる範囲を誤解し、スキップすべきバイト数を間違える。

#### WAVフォーマットの仕様
```
チャンクの構造:
+-------------------+
| chunk_id (4 bytes) | ← これはchunk_sizeに含まれない
+-------------------+
| chunk_size (4 bytes) | ← これもchunk_sizeに含まれない
+-------------------+
| データ部分 (chunk_size bytes) | ← chunk_sizeはこの部分のみ
+-------------------+
```

#### ex28_bin_10aでのバグ
```c
typedef struct {
    char     chunk_id[4];    // 4バイト - chunk_sizeに含まれない
    uint32_t chunk_size;     // 4バイト - chunk_sizeに含まれない
    uint16_t audio_format;   // 以下、chunk_sizeバイト分のデータ
    uint16_t channel_num;
    uint32_t sample_rate;
    uint32_t bytes_rate;
    uint16_t block_align;
    uint16_t bit_depth;      // ここまでで16バイト
} FmtChunk;

// 間違い: sizeof(FmtChunk) = 24バイトを使用
int skip_num = (int)(fmt->chunk_size - (uint32_t)sizeof(FmtChunk));
// chunk_size=18, sizeof(FmtChunk)=24 → skip_num=-6 (負の数!)

// 正しい: chunk_idとchunk_sizeを除いた16バイトと比較
int skip_num = (int)(fmt->chunk_size - (uint32_t)(sizeof(FmtChunk) - 8));
// chunk_size=18, (sizeof(FmtChunk)-8)=16 → skip_num=2 (正しい!)
```

**教訓**:
- `chunk_size`はヘッダ8バイト（chunk_id + chunk_size）を除いた値
- 構造体のサイズとチャンクサイズは異なる概念

---

## 第2部: C言語でよくあるミス

### 2.1 fread()の戻り値チェック間違い

**最頻出エラー**: `fread()`の戻り値を0/1ではなく、読み込んだ要素数として扱う。

#### 間違い (ex28_bin_10a:76)
```c
if (fread(&bin_data, (bit_per_sample / 8), 1, fp) != 0) {
    fprintf(stderr, "search_bin: Cannot read a bin data\n");
    return -1;
}
```

**問題**: `fread()`は成功時に`1`を返すので、`!= 0`は常に真になり、成功してもエラーを返す。

#### 正しい実装
```c
if (fread(&bin_data, (bit_per_sample / 8), 1, fp) != 1) {
    fprintf(stderr, "search_bin: Cannot read a bin data\n");
    return -1;
}
```

**fread()の仕様**:
- `size_t fread(void *ptr, size_t size, size_t nmemb, FILE *stream)`
- 戻り値: **読み込んだ要素数**（成功時は`nmemb`、失敗時は`nmemb`より小さい値）
- `!= 0`ではなく、`!= nmemb`でチェックする

---

### 2.2 符号付き/符号なし整数の比較

**問題**: コンパイラ警告を無視すると実行時に予期しない動作になる可能性がある。

#### 警告が出るコード
```c
if (fmt->chunk_size > sizeof(FmtChunk)) {  // 警告: signed/unsigned comparison
```

- `fmt->chunk_size`: `uint32_t` (符号なし)
- `sizeof(FmtChunk)`: `size_t` (符号なし)

実はこのケースは両方符号なしなので問題ないが、`int32_t`を使っていた場合は危険。

#### 危険な例
```c
int32_t size = -1;  // 負の値
if (size > sizeof(FmtChunk)) {  // 負の値が巨大な正の値に変換される!
    // この分岐が誤って実行される
}
```

**教訓**:
- 符号付き/符号なし整数の混在を避ける
- キャストで明示的に型を統一

---

### 2.3 配列とポインタの混同

**間違い**: 配列のNULLチェック
```c
typedef struct {
    char chunk_id[4];  // 配列
} FmtChunk;

FmtChunk fmt;
if (!fmt.chunk_id) {  // コンパイラ警告: 配列のアドレスは常に非NULL
```

**理由**:
- `fmt.chunk_id`は配列なので、そのアドレスを表す
- 配列のアドレスは**構造体が存在する限り常に有効**

**正しいチェック**:
```c
int is_fmt = 0;  // フラグで管理
// ...
if (!is_fmt) {
    fprintf(stderr, "fmt chunk not found\n");
}
```

---

### 2.4 char vs char[4] の型ミス

**間違った構造体定義** (ex28_bin_10a:18)
```c
typedef struct {
    char     chunk_id[4];
    uint32_t chunk_size;
    char     format;      // ← 1バイトしかない!
} RiffHeader;

// 使用時
memcmp(riff.format, "WAVE", 4);  // エラー: ポインタが必要だが値を渡している
```

**正しい定義**
```c
typedef struct {
    char     chunk_id[4];
    uint32_t chunk_size;
    char     format[4];   // ← 4バイトの配列
} RiffHeader;
```

**教訓**:
- `char`は1バイトの文字、`char[4]`は4バイトの配列
- バイナリフォーマットを扱う際は、仕様と構造体定義を正確に対応させる

---

## 第3部: Pythonでよくあるミス

### 3.1 バイト文字列と文字列の型不一致

**最頻出エラー**: `struct.unpack()`がバイト文字列を返すことを忘れる。

#### 間違い (ex28_bin_9b:37,44,72)
```python
tmp_id, tmp_size, tmp_format = struct.unpack('<4sI4s', tmp)
# tmp_id は b'RIFF' (バイト文字列)

if tmp_id == 'RIFF':  # 常にFalse!
    ...
elif tmp_id == 'fmt ':  # 常にFalse!
    ...
```

#### 正しい実装
```python
# 方法1: バイト文字列リテラルを使う
if tmp_id == b'RIFF' and tmp_format == b'WAVE':
    ...
elif tmp_id == b'fmt ':
    ...

# 方法2: すぐにデコード（推奨）
chunk_id = tmp_id.decode('ascii')
if chunk_id == 'RIFF':
    ...
```

**Pythonの基本**:
```python
b'RIFF' == 'RIFF'   # False (型が違う)
b'RIFF' == b'RIFF'  # True
type(b'RIFF')       # <class 'bytes'>
type('RIFF')        # <class 'str'>
```

**教訓**: `struct.unpack()`の`s`フォーマットは常にバイト文字列を返す。

---

### 3.2 ファイルポインタの計算ミス

**問題** (ex28_bin_9b:45): チャンクヘッダを読んだ後、戻るべきバイト数を間違える。

#### 間違い
```python
tmp = f.read(12)  # 12バイト読む (位置: 0→12)
# tmp = b'fmt \x10\x00\x00\x00\x01\x00\x01\x00'

f.seek(-8, 1)     # 8バイト戻る (位置: 12→4)
                  # これは間違い! chunk_idの途中に戻ってしまう

fmt = f.read(24)  # 24バイト読む (位置: 4→28)
                  # chunk_idの途中から読むので、データがずれる
```

#### 正しい実装
```python
tmp = f.read(12)  # 12バイト読む (位置: 0→12)

f.seek(-12, 1)    # 12バイト全部戻る (位置: 12→0)
                  # chunk_idの先頭に戻る

fmt = f.read(24)  # 24バイト読む (位置: 0→24)
                  # 正しくfmtチャンク全体を読める
```

**教訓**:
- チャンクを最初から読み直す場合は、読んだバイト数を全部戻す
- デバッグ時は`f.tell()`で常に位置を確認

---

## 第4部: デバッグ手法 - 最重要

### 4.1 デバッグ出力がなければ何も見つけられない

**真実**: 目視でコードを何時間読んでも見つけられない問題が、デバッグ出力を入れると5分で見つかる。

#### デバッグ出力の例
```python
def process_read(f):
    pos_before = f.tell()
    tmp = f.read(12)
    pos_after = f.tell()

    # デバッグ出力
    print(f"DEBUG: pos={pos_before}->{pos_after}, bytes={len(tmp)}", file=sys.stderr)
    print(f"DEBUG: data={tmp!r}", file=sys.stderr)

    tmp_id, tmp_size, tmp_format = struct.unpack('<4sI4s', tmp)

    # 型と値をデバッグ
    print(f"DEBUG: tmp_id={tmp_id!r} (type={type(tmp_id).__name__})", file=sys.stderr)
    print(f"DEBUG: tmp_id == 'RIFF'? {tmp_id == 'RIFF'}", file=sys.stderr)
    print(f"DEBUG: tmp_id == b'RIFF'? {tmp_id == b'RIFF'}", file=sys.stderr)
```

**実行結果**:
```
DEBUG: pos=0->12, bytes=12
DEBUG: data=b'RIFF$\x00\x00\x00WAVE'
DEBUG: tmp_id=b'RIFF' (type=bytes)
DEBUG: tmp_id == 'RIFF'? False    ← 問題発見！
DEBUG: tmp_id == b'RIFF'? True
```

このデバッグ出力で**5分以内に問題を特定できる**。

---

### 4.2 デバッグ出力を入れるべき場所

必ず以下の場所にデバッグ出力を入れる:

1. **ファイル読み取りの前後**
   ```c
   fprintf(stderr, "DEBUG: before fread, pos=%ld\n", ftell(fp));
   fread(...);
   fprintf(stderr, "DEBUG: after fread, pos=%ld, read=%zu bytes\n", ftell(fp), n);
   ```

2. **ファイルポインタ移動（seek）の前後**
   ```python
   print(f"DEBUG: before seek, pos={f.tell()}", file=sys.stderr)
   f.seek(-12, 1)
   print(f"DEBUG: after seek, pos={f.tell()}", file=sys.stderr)
   ```

3. **変数の型と値**
   ```python
   print(f"DEBUG: var={var!r}, type={type(var).__name__}", file=sys.stderr)
   ```

4. **比較演算の結果**
   ```python
   print(f"DEBUG: tmp_id == 'RIFF'? {tmp_id == 'RIFF'}", file=sys.stderr)
   ```

5. **ループのイテレーション**
   ```python
   print(f"DEBUG: iteration {i}, fmt={fmt}, data={data}", file=sys.stderr)
   ```

---

### 4.3 小さいテストケースで問題を切り分ける

複雑な問題は、最小限のコードで再現することが重要。

#### テスト例: バイト文字列の比較
```python
# test_bytes_comparison.py
import struct

data = b'RIFF\x00\x00\x00\x00WAVE'
tmp_id, tmp_size, tmp_format = struct.unpack('<4sI4s', data)

print(f"tmp_id = {tmp_id!r}")
print(f"type(tmp_id) = {type(tmp_id)}")
print(f"tmp_id == 'RIFF' → {tmp_id == 'RIFF'}")    # False
print(f"tmp_id == b'RIFF' → {tmp_id == b'RIFF'}")  # True
```

**効果**: 5行のコードで問題の本質を確認できる。

---

## 第5部: よくある間違いチェックリスト

### C言語編

- [ ] `fread()`の戻り値を`!= nmemb`でチェックしているか？
- [ ] 未知チャンクをスキップしているか？
- [ ] `chunk_size`に含まれる範囲を正しく理解しているか？
- [ ] 符号付き/符号なし整数の比較をしていないか？
- [ ] 配列のNULLチェックをしていないか？
- [ ] `char`と`char[4]`を混同していないか？
- [ ] `if-else if-else`構造で排他的な処理になっているか？

### Python編

- [ ] `struct.unpack()`の戻り値をバイト文字列として扱っているか？
- [ ] ファイルポインタの計算が正しいか？（`f.tell()`で確認）
- [ ] 無限ループ防止策（最大反復回数）を入れているか？
- [ ] エラー時に`None`を返すか例外を発生させているか？
- [ ] デバッグ出力を入れているか？

### 共通編

- [ ] デバッグ出力を入れているか？
- [ ] ファイルポインタの位置を追跡しているか？
- [ ] 期待値と実際の値を比較しているか？
- [ ] 小さいテストケースで問題を切り分けているか？
- [ ] コンパイラ警告を無視していないか？

---

## まとめ: 最も重要な3つの教訓

### 1. デバッグ出力を最初から書く習慣

**問題発見時間**: 数時間 → 5分

デバッグ出力があれば:
- 変数の型、値、ファイル位置を常に確認できる
- 期待値と実際の値を比較できる
- 問題の根本原因を**推測ではなく確信**できる

### 2. 未知チャンクを必ずスキップ

バイナリファイル解析の基本パターン:
```c
if (既知のチャンク) {
    // 処理する
} else {
    // スキップする（必須！）
    fseek(fp, chunk_size, SEEK_CUR);
}
```

### 3. 標準ライブラリ関数の仕様を正確に理解

- `fread()`: 読み込んだ**要素数**を返す（0/1ではない）
- `struct.unpack()`: **バイト文字列**を返す（文字列ではない）
- `chunk_size`: ヘッダ8バイトを**除いた**値

---

**作成日**: 2025-12-28
**対象演習**: ex28_bin_8a ~ ex28_bin_10a
**学習テーマ**: WAVファイル解析、デバッグ手法、よくある落とし穴
