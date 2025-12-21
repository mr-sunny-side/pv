#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

/*
	### 12-21: ロジックエラー修正
*/

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

int	get_pixels(FILE *fp, const BmpFileHeader *fh, const BmpInfoHeader *ih,
			int x, int y, Pixel *px)
{
	// x, yのエラーハンドリング
	if (x < 0 || x >= ih->width || y < 0 || y >= ih->height)
		return -1;

	// パディングの計算
	int	bytes_per_pixel = ih->bit_depth / 8;	// ビット深度をbytes単位に変換
	int	row_size = ih->width * bytes_per_pixel;	// 一行当たりのbytesサイズを計算
	int	padding = (4 - (row_size % 4)) % 4;	// 一行当たりのサイズから、4bytes単位でパディングした際のパディング値を算出
	int	padded_row_size = row_size + padding;	// パディング値を含めた一行のサイズを算出

	// Y軸を反転
	int	inverted_y = ih->height - 1 - y;	// x, yはidxなので、0始まりになるようにしている(-1)

	// 指定の座標のoffsetを算出
	long	offset = fh->pixel_offset +		// pixelデータの先頭バイト位置
		      inverted_y * padded_row_size +	// + y座標(反転) * 一行当たりのサイズ(パディング込み) == 先頭からの行バイト距離
		      x * bytes_per_pixel;		// + x座標 * 1ピクセル当たりのバイト値 		    == 該当行の先頭からのバイト距離

	// 該当ファイルアドレスに移動
	if (fseek(fp, offset, SEEK_SET) != 0)
		return 1;


	// Pixel構造体にBGRデータをバッファ
	if (fread(px, sizeof(px), 1, fp) != 1)
		return 1;

	return 0;
}

int	print_all_pixels(FILE *fp, const BmpFileHeader *fh, const BmpInfoHeader *ih) {
	// get_pixels関数をループで呼び出す

	Pixel	px;

	printf("=== All Pixels ===\n");
	printf("\n");

	int	result = 0;

	// 座標はidxなので-1して整合性を取る
	// 座標の全探索は基本的に2重ループになるっぽい
	for (int y = (ih->height - 1); y >= 0; y--) {	// この関数は構造体のポインタしか持ってないので、記述はポインタになる
		for (int x = 0; x < ih->width; x++) {	// xは反転していないので0でok
			if ((result = get_pixels(fp, fh, ih, x, y, &px)) != 0)
				return result;
			printf("[%d, %d, %d] ", px.red, px.green, px.blue);
		}
		printf("\n");
	}

	return 0;
}

int	main(int argc, char **argv) {
	if (argc < 3) {
		fprintf(stderr, "Argument error\n");
		fprintf(stderr, "Usage: [this file] [.bmp] [X coordinate] [Y coordinate]\n");
		fprintf(stderr, "Option: [this file] [.bmp] [-a or --all] to show all pixels\n");
		return 0;
	}

	const char	*file_name = argv[1];
	FILE		*fp = fopen(file_name, "rb");
	BmpFileHeader	fh;
	BmpInfoHeader	ih;


	if (fp == NULL) {
		fprintf(stderr, "main fopen: returned error\n");
		return 1;
	}

	if (fread(&fh, sizeof(fh), 1, fp) != 1) {
		fprintf(stderr, "main fread: returned error\n");
		fclose(fp);
		return 1;
	}


	if (fh.file_type != 0x4d42) {	//
		fprintf(stderr, "File type is not .bmp");
		fclose(fp);
		return -1;
	}

	if (fread(&ih, sizeof(ih), 1, fp) != 1) {
		fprintf(stderr, "main fread: returned error\n");
		fclose(fp);
		return 1;
	}

	int	result = 0;
	if (strcmp(argv[2], "-a") == 0 || strcmp(argv[2], "--all") == 0) {
		result = print_all_pixels(fp, &fh, &ih);
		if (result != 0) {
			fprintf(stderr, "print_all_pixels: returned error\n");
			fclose(fp);
			return result;
		}
		return 0;
	}

	int	x = atoi(argv[2]);
	int	y = atoi(argv[3]);
	Pixel	px;
	result = get_pixels(fp, &fh, &ih, x, y, &px);
	if (result != 0) {
		fprintf(stderr, "get_pixels: returned error\n");
		fclose(fp);
		return result;
	}

	/*
	$ ./pixel_access sample.bmp 0 0
	Pixel at (0, 0):
	  Red:   0 (0x00)
	  Green: 0 (0x00)
	  Blue:  0 (0x00)

	$ ./pixel_access sample.bmp 7 7
	Pixel at (7, 7):
	  Red:   255 (0xFF)
	  Green: 255 (0xFF)
	  Blue:  255 (0xFF)
	*/

	printf("Pixel at (%d, %d):\n", x, y);
	printf("  Red:%10d (0x%02X)\n", px.red, px.red);	// 後ろの16進数の文字数を揃え、labelの文字数で調整している
	printf("  Green:%8d (0x%02X)\n", px.green, px.green);
	printf("  Blue:%9d (0x%02X)\n", px.blue, px.blue);

	fclose(fp);
	return 0;
}
