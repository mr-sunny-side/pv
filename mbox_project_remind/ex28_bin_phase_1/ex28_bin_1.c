#include <stdio.h>
#include <stdint.h>

// データをパディングせず「1byteごとに詰めて保存する」
// また、既存の設定を保存(push)しておく
#pragma pack(push, 1)

typedef struct {
	uint16_t	file_type;
	uint32_t	file_size;
	uint16_t	reserved_1;
	uint16_t	reserved_2;
	uint32_t	pixel_offset;
} BmpFileHeader;

typedef struct {
	uint32_t	header_size;
	int32_t		pixel_width;	// bmpの幅・高さは符号付きで保存する
	int32_t		pixel_hight;
	uint16_t	planes;
	uint16_t	bit_depth;
	uint32_t	compression;
	// 後は使わないので省略
} BmpInfoHeader;

// あらかじめ保存(push)していた既存設定に戻す
// LIFO: Last in First Out 後入れ先出し
#pragma pack(pop)

/*
- ファイルサイズ
- 画像の幅と高さ
- 1ピクセルあたりのビット数
- 圧縮方式
- ピクセルデータへのオフセット
*/

int	main(int argc, char **argv) {

	if (argc != 2) {
		fprintf(stderr, "Argument error\n");
		fprintf(stderr, "Usage: [this file] [.bmp]\n");
		return 1;
	}

	const char	*file_name = argv[1];
	FILE		*fp = fopen(file_name, "rb");
	if (fp == NULL) {
		fprintf(stderr, "Cannot open file\n");
		return 1;
	}

	BmpFileHeader	file_header;
	// バッファする構造体、構造体のサイズ(読み込み量)、バッファの数、読み込むファイル
	// 成功したら、引数のバッファ数を返す
	if (fread(&file_header, sizeof(file_header), 1, fp) != 1) {
		fprintf(stderr, "Cannot read file_header\n");
		fclose(fp);
		return 1;
	}

	// 0x4d42 == BM .bmpかどうか確認
	if (file_header.file_type != 0x4d42) {
		fprintf(stderr, "File is not .bmp\n");
		fclose(fp);
		return 1;
	}

	BmpInfoHeader	info_header;
	if (fread(&info_header, sizeof(info_header), 1, fp) != 1) {
		fprintf(stderr, "Cannot read info_header\n");
		fclose(fp);
		return 1;
	}

	// プレーン数は必ず１なので、それで整合性を確認
	if (info_header.planes != 0x01) { // 16進数で確認！！
		fprintf(stderr, "Plane number is not 1\n");
		fclose(fp);
		return 1;
	}

	/*
	=== BMP File Information ===
	File size: 310 bytes
	Image size: 8 x 8 pixels
	Dimensions: 8 x 8 pixels
	Bits per pixel: 24
	Compression: 0 (0=none)
	Data offset: 54 bytes
	*/

	printf("=== BMP File Information ===\n");
	printf("File size: %d bytes\n", file_header.file_size);
	printf("Image size: %d * %d pixels\n", info_header.pixel_width, info_header.pixel_hight);
	printf("Dimensions: %d * %d pixels\n", info_header.pixel_width, info_header.pixel_hight);
	printf("Bit per pixels: %d\n", info_header.bit_depth);
	if (info_header.compression == 0x00)
		printf("Compression: 0 (0=None)\n");
	else
		printf("Compression: %d\n", info_header.compression);
	printf("Data offset: %d bytes\n", file_header.pixel_offset);
	printf("\n");

	fclose(fp);
	return 0;
}
