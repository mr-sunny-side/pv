# ======================================
# 個人設定（学習用）
# ======================================

# Cコンパイル用エイリアス（42 school形式）
alias 42cc='gcc -Wextra -Wall -Werror'

# C言語静的解析ツール
alias c_file_check='cppcheck --enable=all --suppress=missingIncludeSystem'
alias c_valling='valgrind --leak-check=full --show-leak-kinds=all --track-origins=yes --num-callers=20 -v'

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

# ======================================
# 独自シェルスクリプト
# ======================================

# .mbox_ex用 ファイル実行コマンド
mbox_ex() {
    if [ $# -ne 1 ]; then
        echo "Argument Error"
        echo "mbox_ex [executable file]"
        return 1
    fi

    local prog=$1
    local mbox=$MBOX/google.mbox
    local prog_name=$(basename "$prog")
    local output=$TXT_FILE/${prog_name%.*}.txt

    $prog $mbox > $output

    if [ $? -eq 0 ]; then
        echo "=========="
        echo "✓ Success"
        echo "executable file: $prog_name"
        echo "mbox file: $mbox"
        echo " > $output"
        echo "=========="
    else
        echo "=========="
        echo "✕ Failed"
        echo "executable file: $prog_name"
        echo "mbox file: $mbox"
        echo " > $output"
        echo "=========="
        return 1
    fi
}

# 学習用コンパイルコマンド
compile_ex() {
    if [ $# -ne 1 ]; then
        echo "Argument Error"
        echo "compile_ex [.c file]"
        return 1;
    fi

    local code=$1
    local code_name=$(basename "$code")
    local base_name=${code_name%.c}
    local output=$C_FILE/${base_name}_file

    42cc $code -o $output

    if [ $? -eq 0 ]; then
        echo "=========="
        echo "✓ Success"
        echo "Code file: $code_name"
        echo "Output Path: $output"
        echo "=========="
    else
        echo "=========="
        echo "✕ failed"
        echo "Code file: $code_name"
        echo "Output Path: $output"
        echo "=========="
        return 1;
    fi
}
