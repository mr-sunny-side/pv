#include <stdio.h>
#include <stdint.h>
#include <string.h>

/*
	dataチャンクの特定位置のサンプルを返す

	- dataチャンクまで読み取る
	- サンプリング位置を記録
	- そこからブロックアライン(一回のサンプルごとのデータ量) * 特定位置で計算
*/

#pragma pack(push,1)

typedef struct {
	char		chunk_id[4];
	int32_t		chunk_size;
	char		format;
} RiffHeader;

typedef struct {
	char		chunk_id[4];
	int32_t		chunk_size;
	uint16_t	audio_format;
	uint16_t	channel_num;
	uint32_t	sample_rate;
	uint32_t	bytes_rate;
	uint16_t	block_align;
	uint16_t	bit_depth;
} FmtChunk;

typedef struct {
	char		chunk_id[4];
	uint32_t	chunk_size;
} TmpChunk;

#pragma pack(pop)



int	main(int argc, char **argv) {

	if (argc != 2) {
		fprintf(stderr, "Argument error\n");
		return -1;
	}

	const char	*file_name = argv[1];
	FILE		*fp = fopen(file_name, "rb");
	if (fp == NULL) {
		fprintf(stderr, "main: Cannot open %s", file_name);
		return 1;
	}

	RiffHeader	riff;
	if (fread(&riff, sizeof(riff), 1, fp) != 1) {
		fprintf(stderr, "Cannot read RIFF header");
		return 1;
	}


}
