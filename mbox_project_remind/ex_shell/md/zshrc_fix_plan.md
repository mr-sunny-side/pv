# zshrc.sh の mbox_ex 関数修正プラン

## 問題の分析

[ex_shell/zshrc.sh](../zshrc.sh) の `mbox_ex` 関数が必ず失敗する原因：

1. **40行目**: `local output=$TXT_FILE/${prog}.txt`
2. `$prog` にフルパス（例：`/home/namae/pv/mbox_project_remind/test_case/out/ex26_8_3_file`）が含まれている場合、出力パスが不正になる
3. **結果**: `$TXT_FILE//home/namae/pv/mbox_project_remind/test_case/out/ex26_8_3_file.txt`
4. このパスは存在しないため、42行目のリダイレクトが失敗し、終了ステータスが非ゼロになる

## 問題の具体例

### 現在の動作
```bash
# 関数呼び出し
mbox_ex /home/namae/pv/mbox_project_remind/test_case/out/ex26_8_3_file /home/namae/pv/mbox_project_remind/mbox/google.mbox

# 生成される出力パス（不正）
/home/namae/pv/mbox_project_remind/test_case/txt//home/namae/pv/mbox_project_remind/test_case/out/ex26_8_3_file.txt
```

## 解決方法

`$prog` からベースネーム（ディレクトリパスを除いたファイル名）のみを抽出して、出力ファイル名を構築する。

## 実装プラン

### 修正対象ファイル
- [ex_shell/zshrc.sh](../zshrc.sh)

### 必要な変更

`mbox_ex` 関数内（31〜54行目）：

**38〜40行目を修正**:
```bash
# 修正前
local prog=$1
local mbox=$2
local output=$TXT_FILE/${prog}.txt

# 修正後
local prog=$1
local mbox=$2
local prog_name=$(basename "$prog")  # ファイル名のみを抽出
local output=$TXT_FILE/${prog_name}.txt
```

### 変更の効果

- **修正前**: フルパスがそのまま使用され、不正なパスが生成される
- **修正後**: ファイル名のみが使用され、正しいパスが生成される
  ```
  正しい出力パス: /home/namae/pv/mbox_project_remind/test_case/txt/ex26_8_3_file.txt
  ```

## テスト手順

修正後、以下のコマンドでテスト：

```bash
# スクリプトを再読み込み
source /home/namae/pv/mbox_project_remind/ex_shell/zshrc.sh

# 関数を実行
mbox_ex /home/namae/pv/mbox_project_remind/test_case/out/ex26_8_3_file /home/namae/pv/mbox_project_remind/mbox/google.mbox
```

### 期待される結果

```
✓ Success
argv[1] /home/namae/pv/mbox_project_remind/test_case/out/ex26_8_3_file
argv[2] /home/namae/pv/mbox_project_remind/mbox/google.mbox
 > /home/namae/pv/mbox_project_remind/test_case/txt/ex26_8_3_file.txt
```

出力ファイルが `$TXT_FILE/ex26_8_3_file.txt` に正常に作成される。
