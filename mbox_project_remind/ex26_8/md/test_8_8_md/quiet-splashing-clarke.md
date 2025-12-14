# test_8_8.py の問題分析

## 修正済みの問題
- [x] 76行目の後に `continue` を追加 → 修正済み
- [x] `b''` への修正 → 修正済み

## 本当の原因: ctypes の c_char_p の落とし穴（クラッシュの原因）

**エラー**: `munmap_chunk(): invalid pointer` → 不正なポインタを free しようとしている

### 問題の説明

```python
lib.ext_domain.restype = ctypes.c_char_p  # ← これが問題！
```

`c_char_p` を戻り値の型に設定すると、ctypes は**自動的にPython の bytes オブジェクトに変換**します。

つまり:
1. C の `ext_domain()` が `malloc()` でメモリを確保し、ポインタを返す
2. ctypes がそのポインタを **Python の bytes にコピー**
3. `raw_domain` は bytes オブジェクト（元のポインタではない）
4. `lib.free_memory(raw_domain)` を呼ぶと、Python が**新しい一時的な C 文字列**を作成
5. その一時的なポインタを free しようとする → **クラッシュ**

### 修正方法

`c_void_p` を使ってポインタを保持し、`ctypes.string_at()` で文字列を読み取る:

#### 変更箇所1: [test_8_8.py:66-69](ex26_8/ex26_8_8/test_8_8.py#L66-L69)
```python
# Before:
lib.ext_domain.restype = ctypes.c_char_p
lib.free_memory.argtypes = [ctypes.c_char_p]

# After:
lib.ext_domain.restype = ctypes.c_void_p    # ポインタを保持
lib.free_memory.argtypes = [ctypes.c_void_p]  # ポインタを受け取る
```

#### 変更箇所2: [test_8_8.py:84-89](ex26_8/ex26_8_8/test_8_8.py#L84-L89)
```python
# Before:
raw_domain = lib.ext_domain(raw_email)
email = raw_email.decode()
if raw_domain:
    domain = raw_domain.decode()

# After:
raw_domain_ptr = lib.ext_domain(raw_email)  # void* ポインタ
email = raw_email.decode()
if raw_domain_ptr:
    domain = ctypes.string_at(raw_domain_ptr).decode()  # ポインタから文字列を読む
    print(f"{email:<40}->{domain:>40}")
    lib.free_memory(raw_domain_ptr)  # 元のポインタを正しく free
```

## 修正が必要なファイル

- **test_8_8.py** のみ（2箇所）
