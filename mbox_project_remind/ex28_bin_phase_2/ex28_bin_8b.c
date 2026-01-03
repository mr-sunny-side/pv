#include <stdio.h>
#include <stdint.h>
#include <string.h>

/*

	1. fmtチャンクを保存する構造体を作成
	※ 今回はRIFFのidの直後にfmtが来る前提で書く

*/
#pragma pack(push, 1)

typedef	struct {
	char		chunk_id[4];
	uint32_t	chunk_size;
	char		chunk_format[4];
} RiffHeader;

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

/*
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

void	print_result(const FmtChunk *fmt) {

	uint16_t	ft_block_align = fmt->channel_num * (fmt->bit_depth / 8);		// 一回のサンプリングで記録されるデータ量（bytes）

	printf("=== fmt Chunk ===\n");
	printf("Audio format: %u (%s)\n", fmt->audio_format,
		fmt->audio_format == 1 ? "PCM" : "Unknown");
	printf("Channels: %u (%s)\n", fmt->channel_num,
		fmt->channel_num == 1 ? "Mono" : "Stereo");
	printf("Sample rate: %u Hz\n", fmt->sample_rate);
	printf("Bit per sample: %u\n", fmt->bit_depth);
	printf("Block align: %u bytes\n", fmt->block_align);
	printf("\n");

	printf("=== Block Align Verification ===\n");
	printf("- 一秒間に何bytes記録するか?\n");
	printf("\n");
	printf("Formula: channels * (bit depth / 8)\n");
	printf("Calculate: %u * (%u / 8)\n", fmt->channel_num, fmt->bit_depth);
	printf("Result: %s\n", fmt->block_align == ft_block_align ? "✓" : "✕");
}

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

	RiffHeader	riff;
	if (fread(&riff, sizeof(riff), 1, fp) != 1) {
		fprintf(stderr, "Cannot read the file\n");
		fclose(fp);
		return 1;
	}

	if (memcmp(riff.chunk_id, "RIFF", 4) != 0 ||
		memcmp(riff.chunk_format, "WAVE", 4) != 0) {
		fprintf(stderr, "This file is not WAV file\n");
		fclose(fp);
		return -1;
	}

	FmtChunk	fmt;
	if (fread(&fmt, sizeof(fmt), 1, fp) != 1) {
		fprintf(stderr, "Cannot read the file\n");
		fclose(fp);
		return 1;
	}

	if (memcmp(fmt.chunk_id, "fmt ", 4) != 0) {
		fprintf(stderr, "This is not fmt chunk: %.4s", fmt.chunk_id);
		fclose(fp);
		return 1;
	}

	print_result(&fmt);
	fclose(fp);
	return 0;


}
