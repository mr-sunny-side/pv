# ======================================
# 個人設定（学習用）
# ======================================

# Cコンパイル用エイリアス（42 school形式）
alias 42cc='gcc -Wextra -Wall -Werror'

# C言語静的解析ツール
alias c_file_check='cppcheck --enable=all --suppress=missingIncludeSystem'

# ======================================
# プロジェクト用環境変数
# ======================================

# mbox解析プロジェクトのルートディレクトリ
export MBOX_PROJECT="$HOME/pv/mbox_project_remind"

# プロジェクト内のディレクトリ
export C_FILE="$MBOX_PROJECT/test_case/out"
export TXT_FILE="$MBOX_PROJECT/test_case/txt"
export MBOX="$MBOX_PROJECT/mbox"

# ======================================
# 外部ツールのパス設定
# ======================================

# pipx（Pythonツール）をパスに追加
export PATH="$PATH:$HOME/.local/bin"

# .mbox_ex用 実行コマンド
mbox_ex() {
    if [ $# -ne 2 ]; then
        echo "Argument Error"
        echo "func_ex [executable file] [file argv]"
        return 1
    fi

    local prog=$1
    local mbox=$2
    local prog_name=$(basename "$prog")
    local output=$TXT_FILE/${prog_name}.txt

    $prog $mbox > $output

    if [ $? -eq 0 ]; then
        echo "✓ Success"
        echo "argv[1] $prog"
        echo "argv[2] $mbox"
        echo " > $output"
    else
        echo "✕ Failed"
        echo "$prog $mbox > $output"
        return 1
    fi
}
