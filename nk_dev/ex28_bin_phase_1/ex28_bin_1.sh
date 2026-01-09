#!/bin/bash

ft_hexdump() {

    local sh="$0"
    local bin="$1"
    local mbox="$2"

    echo ""
    echo "=== $(basename "$0") ==="
    hexdump -C $sh | head -4
    echo ""
    echo "=== $(basename "$1") ==="
    hexdump -C $bin | head -4
    echo ""
    echo "=== $(basename "$2") ==="
    hexdump -C $mbox | head -4
    echo ""

    if [ $? -ne 0 ]; then
        echo $?
        return 1
    fi

    return 0
}

if [ "${BASH_SOURCE[0]}" == "${0}" ]; then

    if [ $# -ne 2 ]; then
        echo "Argument Error"
        echo "Usage: [This .sh] [.bmp] [.mbox]"
        exit 1
    fi

    ft_hexdump $1 $2
    exit $?

fi
