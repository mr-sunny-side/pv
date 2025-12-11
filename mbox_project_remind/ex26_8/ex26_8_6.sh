ex26_8_ex () {

    if [ $# -ne 1 ]; then
        echo "Argument Error"
        return 1
    fi

    local prog=$1
    local prog_c=$C_FILE/${prog}_file
    local prog_py=$MBOX_PROJECT/ex26_8/${prog}.py
    local mbox=$MBOX/google.mbox
    local output=$MBOX_PROJECT/ex26_8/txt/${prog}_sh.txt

    echo "========== C result ==========" > $output
    echo "" >> $output

    for i in {1..5}; do
        ($prog_c $mbox 2>&1) | grep "Processing Time" >> $output;
    done

    echo "" >> $output
    echo "========== Python result ==========" >> $output
    echo "" >> $output

    for i in {1..5}; do
        (python3 $prog_py $mbox 2>&1) | grep "Processing Time" >> $output;
    done

    return 0
}
