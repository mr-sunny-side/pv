#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

#pragma pack(push, 1)
typedef	struct {
	uint16_t	file_type;
	uint32_t	file_size;
	uint16_t	reserved_1;
	uint16_t	reserved_2;
	uint16_t	pixel_offset;
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
#pragma pack(pop)

typedef	struct {
	uint8_t	red;
	uint8_t	green;
	uint8_t	blue;
} Pixel;

// 計算部分の復習用
int	get_pixels(FILE *fp, BmpFileHeader *fh, BmpInfoHeader *ih, int x, int y,Pixel *px) {

	if (x < 0 || x >= ih->width || y < 0 || y >= ih->height)
		return -1;

	int	bytes_per_pixel = ih->bit_depth / 8;		// 1ビットあたりのバイト数
	int	bytes_per_line = ih->width * bytes_per_pixel;	// 一行あたりのバイト数
	int	padding = 4 - (bytes_per_line % 4);		// 一行4バイトパディングの際、必要なパディング

	int	reversed_y = ih->height - y - 1;		// bmpはyが反転しているので、その計算

	long	offset = fh->pixel_offset +			// 前提としてこの式は「pixel_offsetから幾つスキップするか」なので、
			(bytes_per_line + padding) * reversed_y +	// ーそれぞれの計算の始まりは0になる
			bytes_per_pixel * x;
}

int	turn_to_gray(FILE *fp, BmpFileHeader *fh, BmpInfoHeader *ih, Pixel *px) {

	// 引数のpxをグレースケールにして可否をreturn
	// mainでループ -> get_pixels -> turn_to_gray -> 何らかの形で保存 or 毎回書き込み(fopenだったらバッファするからいいか？)

	/* 輝度 = 0.299 * R + 0.587 * G + 0.114 * B */
}

int	main(int argc, char **argv) {
	if (argc != 3) {
		fprintf(stderr, "Argument error\n");
		fprintf(stderr, "Usage: [this file] [.bmp] [output path]\n");
		fprintf(stderr, "       This file make .bmp file gray color\n");
		return -1;
	}

	const char	*input = argv[1];
	const char	*output = argv[2];
	FILE		*fp = fopen(input, "rb");
	if (fp == NULL) {
		fprintf(stderr, "Cannot open the file\n");
		return 1;
	}

	BmpFileHeader	fh;
	BmpInfoHeader	ih;
	if (fread(&fh, sizeof(fh), 1, fp) != 1) {
		fprintf(stderr, "fread/main: returned error\n");
		return 1;
	}

	if (fh.file_type != 0x4d42) {
		fprintf(stderr, "Input file is not .bmp\n");
		return -1;
	}

	if (fread(&ih, sizeof(ih), 1, fp) != 1) {
		fprintf(stderr, "fread/main: returned error\n");
		return 1;
	}

	// ループ
}
