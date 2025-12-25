#include <stdio.h>
#include <stdint.h>
#include <string.h>

/*

	1. fmtチャンクを保存する構造体を作成
	※ 今回はRIFFのidの直後にfmtが来る前提で書く

	=== fmt Chunk ===
	Audio format: 1 (PCM)
	Channels: 1 (Mono)
	Sample rate: 44100 Hz
	Bits per sample: 16
	Block align: 2 bytes

	=== Block Align Verification ===
	Formula: channels × (bits_per_sample / 8)
	Calculation: 1 × (16 / 8) = 2
	File value: 2
	Match: ✓
*/
#pragma pack(push, 1)

typedef	struct {
	char		chunk_id[4];
	uint32_t	chunk_size;
	char		chunk_format[4];
} TmpChunkHeader;

typedef	struct {
	char		chunk_id[4];
	uint32_t	chunk_size;
	uint16_t	audio_format;
	uint16_t	channel_num;
	uint32_t	sample_rate;
	uint32_t	byte_rate;
	uint16_t	block_align;
	uint16_t	bit_depth;
} FmtChunk;

#pragma pack(pop)

int	main(int argc, char **argv) {

	if (argc != 2) {
		fprintf(stderr, "Argument error\n");
		return -1;
	}

	const char	*file_name = argv[1];
	FILE		*fp = fopen(file_name, "rb");
	if (fp == NULL) {
		fprintf(stderr, "Cannot open file\n");
		return 1;
	}

	TmpChunkHeader tmp_chh;
	if (fread(&tmp_chh, sizeof(tmp_chh), 1, fp) != 1) {
		fprintf(stderr, "Cannot read the file\n");
		fclose(fp);
		return 1;
	}

	if (memcmp(tmp_chh.chunk_id, "RIFF", 4) != 0 ||
		memcmp(tmp_chh.chunk_format, "WAVE", 4) != 0) {
		fprintf(stderr, "This file is not WAV file\n");
		fclose(fp);
		return -1;
	}

	if (fread(&tmp_chh, sizeof(tmp_chh), 1, fp) != 1) {
		fprintf(stderr, "Cannot read the file\n");
		fclose(fp);
		return 1;
	}




}
