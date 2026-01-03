# compile_ex関数の出力ファイル名修正方法

## 問題の説明

現在の`compile_ex`関数は、以下のような動作をします：

```bash
compile_ex ex26_8/ex26_8_5_cli_tool.c
✓ Success
Code file: ex26_8_5_cli_tool.c
Output Path: /home/namae/pv/mbox_project_remind/test_case/out/ex26_8_5_cli_tool.c_file
```

**期待する動作:**
- 出力ファイル名: `ex26_8_5_file`（`ex26_8_5_cli_tool.c_file`ではなく）

## 解決方法

### 現在のコード（zshrc.sh 73行目）

```bash
local output=$C_FILE/${code_name}_file
```

### 修正案

```bash
local base_name=${code_name%.c}           # .c 拡張子を除去
local output=$C_FILE/${base_name%_*}_file  # 最後の _ 以降を削除して _file を追加
```

## 処理の詳細

### シェルパラメータ展開の説明

1. **`${code_name%.c}`**: 末尾の`.c`を除去
   - 例: `ex26_8_5_cli_tool.c` → `ex26_8_5_cli_tool`

2. **`${base_name%_*}`**: 最後のアンダースコア`_`以降を削除
   - 例: `ex26_8_5_cli_tool` → `ex26_8_5`

3. **`_file`を追加**
   - 例: `ex26_8_5` → `ex26_8_5_file`

### 処理フロー図

```
入力: ex26_8_5_cli_tool.c
  ↓ basename
ex26_8_5_cli_tool.c
  ↓ ${code_name%.c}
ex26_8_5_cli_tool
  ↓ ${base_name%_*}
ex26_8_5
  ↓ _file を追加
ex26_8_5_file
```

## 他のファイル例

この修正により、以下のような変換が行われます：

| 入力ファイル名 | 出力実行ファイル名 |
|--------------|-----------------|
| `ex26_8_1_read_file.c` | `ex26_8_1_file` |
| `ex26_8_2_filter_lines.c` | `ex26_8_2_file` |
| `ex26_8_3_dynamic_buffer.c` | `ex26_8_3_file` |
| `ex26_8_4_extract_email.c` | `ex26_8_4_file` |
| `ex26_8_5_cli_tool.c` | `ex26_8_5_file` |

## 完全な修正後の関数

```bash
# 学習用コンパイルコマンド
compile_ex() {
    if [ $# -ne 1 ]; then
        echo "Argument Error"
        echo "compile_ex [.c file]"
        return 1;
    fi

    local code=$1
    local code_name=$(basename "$code")
    local base_name=${code_name%.c}           # .c を除去
    local output=$C_FILE/${base_name%_*}_file  # 最後の _ 以降を削除して _file を追加

    42cc $code -o $output

    if [ $? -eq 0 ]; then
        echo "✓ Success"
        echo "Code file: $code_name"
        echo "Output Path: $output"
    else
        echo "✕ failed"
        echo "Code file: $code_name"
        echo "Output Path: $output"
        return 1;
    fi
}
```

## 注意点

- **`-o`オプションの追加**: `42cc $code -o $output`で出力先を明示的に指定
- **実行ファイルに拡張子は不要**: Linuxでは実行ファイルに拡張子をつける必要はありません

## 修正ファイル

- `ex_shell/zshrc.sh` の73行目付近
