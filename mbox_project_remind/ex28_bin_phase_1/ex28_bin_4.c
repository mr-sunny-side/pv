#include <stdio.h>
#include <stdint.h>
#include <string.h>

#pragma pack(push, 1)
typedef	struct {
	uint16_t	file_type;
	uint32_t	file_size;
	uint16_t	reserved_1;
	uint16_t	reserved_2;
	uint32_t	pixel_offset;
} BmpFileHeader;

typedef	struct {
	uint32_t	header_size;
	int32_t		width;
	int32_t		height;
	uint16_t	planes;
	uint16_t	bit_depth;
	uint32_t	compression;
	// 省略
} BmpInfoHeader;
#pragma pack(pop) // Pixel構造体はデータ保管用なのでパディングok

// BGRを読み込むバッファ
// 0ー255なので、1色1byte
typedef	struct {
	uint8_t	blue;
	uint8_t	green;
	uint8_t	red;
} Pixel;

/*
	### get_pixel関数の要件

	1. ファイル情報から指定のピクセル座標まで移動
	2. BGR情報を取得し、Pixel構造体に直接格納
*/

int	get_pixel(FILE *fp, const BmpFileHeader *fh, const BmpInfoHeader *ih,
			int x, int y, Pixel *px)
{
	// x, yのエラーハンドリング
	if (x < 0 || x >= ih->width || y < 0 || y >= ih->height) {
		fprintf(stderr, "get_pixel: Invalid Number\n");
		return -1;
	}

	// パディングの計算
	int bytes_per_pixel = ih->bit_depth / 8;	// ビット深度をbytes単位に変換
	int row_size = ih->width * bytes_per_pixel;	// 一行当たりのbytesサイズを計算
	int padding = (4 - (row_size % 4)) % 4;		// 一行当たりのサイズから、4bytes単位でパディングした際のパディング値を算出
	int padded_row_size = row_size + padding;	// パディング値を含めた一行のサイズを算出

	// Y軸を反転
	int inverted_y = ih->height - 1 - y;		// x, yはidxなので、0始まりになるようにしている(-1)

	// 指定の座標のoffsetを算出
	long offset = fh->pixel_offset +		// pixelデータの先頭バイト位置
		      inverted_y * padded_row_size +	// + y座標(反転) * 一行当たりのサイズ(パディング込み) == 先頭からの行バイト距離
		      x * bytes_per_pixel;		// + x座標 * 1ピクセル当たりのバイト値 		    == 該当行の先頭からのバイト距離

	// 該当ファイルアドレスに移動
	if (fseek(fp, offset, SEEK_SET) != 0) {
		fprintf(stderr, "fseek returned error\n");
		return 1;
	}

	if (fread(px, sizeof(px), 1, fp) != 1) {
		fprintf(stderr, )
	}


}
