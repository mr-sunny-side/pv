#!/bin/bash
# WAVファイルの構造を視覚化

if [ $# -lt 1 ]; then
    echo "Usage:$0 <wav_file>"
    exit 1
fi

file="$1"

echo "=== WAV File Structure Analysis ==="
echo ""

# ファイル全体のサイズ
file_size=$(stat -c %s "$file" 2>/dev/null || stat -f %z "$file" 2>/dev/null)
echo "File size:$file_size bytes"
echo ""

# RIFFチャンク (オフセット 0-11)
echo "=== RIFF Chunk (offset 0-11) ==="
hexdump -C -n 12 "$file"
echo ""

# fmtチャンク (オフセット 12-35)
echo "=== fmt Chunk (offset 12-35) ==="
hexdump -C -s 12 -n 24 "$file"
echo ""

# dataチャンクヘッダー (オフセット 36-43)
echo "=== data Chunk Header (offset 36-43) ==="
hexdump -C -s 36 -n 8 "$file"
echo ""

# サンプルデータの最初の64バイト (オフセット 44-)
echo "=== Sample Data (first 64 bytes, offset 44-107) ==="
hexdump -C -s 44 -n 64 "$file"
echo ""
