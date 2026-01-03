#include <stdio.h>
#include <stdint.h>
#include <string.h>	// memcmpに必要

#pragma pack(push,1)

typedef	struct {
	char		chunk_id[4];
	uint32_t	file_size;
	char		format[4];
} RiffHeader;

#pragma pack(pop)

/*
=== RIFF Header ===
Chunk ID: RIFF
Chunk size: 90660 bytes
Format: WAVE

✓ This is a valid WAV file.
*/

void	print_header(const RiffHeader *fh) {

	printf("=== RIFF Header ===\n");
	printf("Chunk ID: %.4s\n", fh->chunk_id);	// バイト配列なのでNULLがない よって出力文字数を指定する
	printf("Chunk size: %u\n", fh->file_size);	// 符号なし整数の出力指定子 厳密にはinttypes.hを使うべき
	printf("Format: %.4s\n", fh->format);
}

int	main(int argc, char **argv) {

	if (argc != 2) {
		fprintf(stderr, "Argument error\n");
		fprintf(stderr, "Usage: [this file] [.wav]\n");
		return -1;
	}

	const char	*file_name = argv[1];
	FILE		*fp = fopen(file_name, "rb");
	if (fp == NULL) {
		fprintf(stderr, "Cannot open %s\n", file_name);
		return 1;
	}

	RiffHeader fh;
	if (fread(&fh, sizeof(fh), 1, fp) != 1) {
		fprintf(stderr, "fread/main returned error\n");
		fclose(fp);
		return 1;
	}

	if (memcmp(fh.chunk_id, "RIFF", 4) != 0) {
		fprintf(stderr, "memcmp/main: This is not RIFF file\n");
		fprintf(stderr, "header.chunk_id: %.4s\n", fh.chunk_id);
		return -1;
	}

	if (memcmp(fh.format, "WAVE", 4) != 0) {
		fprintf(stderr, "memcmp/main: This is not WAVE file\n");
		fprintf(stderr, "header.format: %.4s\n", fh.format);
		return -1;
	}

	print_header(&fh);
	fclose(fp);
	return 0;
}
