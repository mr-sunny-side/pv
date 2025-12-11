#!/bin/bash

: <<'COMMENT'
独立した実行scriptとして以下の関数を使用できるように、この.shを記述する
以下の関数はzshrcと独立して、このファイルが実行された際にのみ定義されること
独立するために環境変数はファイル内で定義
12-11: scriptの詳細な分析を行う Notionに記載
COMMENT

# mbox解析プロジェクトのルートディレクトリ
export MBOX_PROJECT="$HOME/pv/mbox_project_remind"

# プロジェクト内のディレクトリ
export C_FILE="$MBOX_PROJECT/test_case/out"
export TXT_FILE="$MBOX_PROJECT/test_case/txt"
export MBOX="$MBOX_PROJECT/mbox"

ex26_8_ex () {

    local prog="$1"
    local prog_c="$C_FILE/${prog}_file"
    local prog_py="$MBOX_PROJECT/ex26_8/${prog}.py"
    local mbox="$MBOX/google.mbox"
    local output="$MBOX_PROJECT/ex26_8/txt/${prog}_sh.txt"

    echo "========== C result ==========" > $output
    echo "" >> $output

    for i in {1..5}; do
        ("$prog_c" "$mbox" 2>&1) | grep "Processing Time" >> $output;
        if [ $? -ne 0 ]; then
            echo "✕ Program Failed" >&2
            echo "Executable File: $prog_c" >&2
            return 1
        fi
    done

    echo "" >> $output
    echo "========== Python result ==========" >> $output
    echo "" >> $output

    for i in {1..5}; do
        (python3 "$prog_py" "$mbox" 2>&1) | grep "Processing Time" >> $output;
        if [ $? -ne 0 ]; then
            echo "✕ Program Failed" >&2
            echo "Executable File: $prog_py" >&2
            return 1
        fi
    done

    echo "✓ Success"
    echo ""
    cat $output

    return 0
}

if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    if [ $# -ne 1 ]; then
        echo "Argument Error" >&2
        echo "Usage: [$0] [ex Number]" >&2

        # exitはscriptの終了
        # この場合、このscript全体を終了しても問題ないし必要
        exit 1
    fi

    ex26_8_ex $1

    # 呼び出した関数の戻り値をそのまま終了ステータスとして表示
    exit $?
fi
