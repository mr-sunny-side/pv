#include <stdio.h>
#include <stdint.h>
#include <string.h>

/*
	12-27: 完全パーサーを設計する

	=== WAV File Information ===
	Audio format: 1 (PCM)
	Channels: 1 (Mono)
	Sample rate: 44100 Hz
	Bits per sample: 16
	Data size: 88200 bytes
	Duration: 1.00 seconds

	:4  "fmt " (チャンクID、スペース含む)
	:4  チャンクサイズ（通常16）
	:2  オーディオフォーマット（1=PCM）
	:2  チャンネル数（1=モノラル、2=ステレオ）
	:4  サンプリングレート（Hz）
	:4  バイトレート
	:2  ブロックアライン
	:2  ビット深度
*/

#pragma pack(push, 1)

typedef	struct {
	char		chunk_id[4];
	uint32_t	chunk_size;
} TmpChunk;

typedef	struct {
	char		chunk_id[4];
	uint32_t	chunk_size;
	char		format[4];
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

int	process_fread(FILE *fp, FmtChunk *fmt, TmpChunk *tmp, int *fmt_count, int *data_count, uint32_t *data_size) {

	if (fread(tmp, sizeof(*tmp), 1, fp) != 1) {
		fprintf(stderr, "fread/process_fread: returned error\n");
		return 1;
	}

	if (memcmp(tmp->chunk_id, "fmt ", 4) == 0) {
		fseek(fp, -sizeof(*tmp), SEEK_CUR);		//fmt構造体に読み込む & エラーハンドリング
		if (fread(fmt, sizeof(*fmt), 1, fp) != 1)
			return 1;
		*fmt_count = 1;

		int	skip_num = fmt->chunk_size - sizeof(FmtChunk);
		if (fmt->chunk_size > sizeof(FmtChunk)) {
			fseek(fp, skip_num, SEEK_CUR);
			fprintf(stderr, "Unknown chunk is skiped\n");
		}
	}

	if (memcmp(tmp->chunk_id, "data", 4) == 0) {
		*data_size = tmp->chunk_size;
		*data_count = 1;
	}

	return 0;
}

int	main(int argc, char **argv) {

	if (argc != 2) {
		fprintf(stderr, "Argument error\n");
		return -1;
	}

	const char	*file_name =argv[1];
	FILE		*fp = fopen(file_name, "rb");
	if (fp == NULL) {
		fprintf(stderr, "Cannot open %s\n", file_name);
		return 1;
	}

	RiffHeader	riff;
	if (fread(&riff, sizeof(riff), 1, fp) != 1) {
		fprintf(stderr, "fread/main: returned error\n");
		fclose(fp);
		return 1;
	}

	if (memcmp(riff.chunk_id, "RIFF", 4) != 0 ||
		memcmp(riff.format, "WAVE", 4) != 0) {

		fprintf(stderr, "This file is not WAV\n");
		return -1;
	}

	int		fmt_count = 0;
	int		data_count = 0;
	int		result =0;
	uint32_t	data_size = 0;
	FmtChunk	fmt = {0};
	TmpChunk	tmp = {0};
	while (!fmt_count || !data_count) {
		result = process_fread(fp, &fmt, &tmp, &fmt_count, &data_count, &data_size);
		if (result != 0) {
			fprintf(stderr, "process_fread/main: returned error\n");
			fclose(fp);
			return result;
		}
	}

	if (!fmt_count || !data_count) {
		fprintf(stderr, "Cannot find fmt or data chunk\n");
		fclose(fp);
		return 1;
	}

	/*
	=== WAV File Information ===
	Audio format: 1 (PCM)
	Channels: 1 (Mono)
	Sample rate: 44100 Hz
	Bits per sample: 16
	Data size: 88200 bytes
	Duration: 1.00 seconds
	*/

	printf("\n=== WAV File Information ===\n");
	printf("Audio format: %u (%s)\n", fmt.audio_format,
		fmt.audio_format == 1 ? "PCM" : "Unknown");
	printf("Channels: %u (%s)\n", fmt.channel_num,
		fmt.channel_num == 1 ? "Mono" : "Stereo");
	printf("Sample rate: %u Hz\n", fmt.sample_rate);

	// 構造を理解するために自分で計算する
	uint16_t	bit_per_sample = fmt.bit_depth * fmt.channel_num;
	printf("Bit per sample: %u\n", bit_per_sample);

	float		duration = (float)data_size / (bit_per_sample / 8 * fmt.sample_rate);
	printf("Duration: %.2f\n", duration);
	printf("\n");

	fclose(fp);
	return 0;
}
