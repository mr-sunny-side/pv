#include <stdio.h>
#include <stdint.h>
#include <string.h>

// **目的**: 最大振幅、ゼロクロスを1回の走査で計算する(余裕があればRMS)
// 01-03: process_read関数の作成から

#pragma pack(push, 1)

typedef	struct {
	char		chunk_id[4];
	uint32_t	chunk_size;
}	TmpHeader;

typedef	struct {
	char		chunk_id[4];
	uint32_t	chunk_size;
	char		format[4];
}	RiffHeader;

typedef	struct {
	char		chunk_id[4];
	uint32_t	chunk_size;
	uint16_t	audio_format;
	uint16_t	channel_num;
	uint32_t	sample_rate;
	uint32_t	byte_rate;
	uint16_t	block_align;
	uint16_t	bit_depth;
}	FmtChunk;

int	process_read(FILE *fp, FmtChunk *fmt, TmpHeader *tmp,int *is_fmt, uint32_t *data_size, long *data_offset) {

	if (fread(tmp, sizeof(TmpHeader), 1, fp) != 1) {
		fprintf(stderr, "ERROR fread/process_read: Cannot read TmpHeader\n");
		return -1;
	}


}

int	main(int argc, char **argv) {

	if (argc != 2) {
		fprintf(stderr, "ERROR main: Argument error\n");
		return -1;
	}

	const char	*file_name = argv[1];
	FILE		*fp = fopen(file_name, "rb");
	if (fp == NULL) {
		fprintf(stderr, "ERROR fopen/main: Cannot open %s\n", file_name);
		return -1;
	}

	RiffHeader	riff;
	if (fread(&riff, sizeof(RiffHeader), 1, fp) != 1) {
		fprintf(stderr, "ERROR fread/main: Cannot read RIFF header\n");
		return -1;
	}

	if (memcmp(riff.chunk_id, "RIFF", 4) != 0 ||
		memcmp(riff.format, "WAVE", 4) != 0) {
		fprintf(stderr, "ERROR main: This file is not WAV\n");
		return -1;
	}


}
