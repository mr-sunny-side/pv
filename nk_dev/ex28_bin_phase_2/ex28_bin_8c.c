#include <stdio.h>
#include <stdint.h>
#include <string.h>

/*
	12-26: riff, fmt, dataチャンクを読み取るコードを書く
	1. fmtチャンクまで読む
	2. fmtチャンクは情報だけなので、その終端からそのままdataチャンクを読む
	3. dataヘッダーで生データのサイズが分かるので、計算

*/

#pragma pack(push, 1)

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
	uint32_t	bytes_rate;
	uint16_t	block_align;
	uint16_t	bit_depth;
} FmtChunk;

typedef	struct {
	char		chunk_id[4];
	uint32_t	chunk_size;
} DataHeader;

#pragma pack(pop)

int	main(int argc, char **argv) {

	if (argc != 2) {
		fprintf(stderr, "Argument error\n");
		return -1;
	}

	const char	*file_name = argv[1];
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

	if  (memcmp(riff.chunk_id, "RIFF", 4) != 0 ||
		memcmp(riff.format, "WAVE", 4) != 0) {

		fprintf(stderr, "This file is not WAV\n");
		fclose(fp);

		return -1;
	}

	FmtChunk	fmt;
	if (fread(&fmt, sizeof(fmt), 1, fp) != 1) {
		fprintf(stderr, "fread/main: returned error\n");
		fclose(fp);

		return 1;
	}

	if (memcmp(fmt.chunk_id, "fmt ", 4) != 0) {
		fprintf(stderr, "Cannot find fmt chunk\n");
		fclose(fp);

		return 1;
	}

	DataHeader	data;
	if (fread(&data, sizeof(data), 1, fp) != 1) {
		fprintf(stderr, "fread/main: returned error\n");
		fclose(fp);

		return 1;
	}

	if (memcmp(data.chunk_id, "data", 4) != 0) {
		fprintf(stderr, "Cannot find data chunk\n");
		fclose(fp);

		return 1;
	}

	/*
	=== data Chunk ===
	Data size: 88200 bytes

	=== Sample Count Calculation ===
	Formula: data_size / block_align
	Meaning: 何回サンプリングしたか？
	Calculation: 88200 / 2 = 44100 samples

	=== Duration Calculation ===
	Formula: num_samples / sample_rate
	Meaning: 何秒サンプリングしたか？（何秒のデータか）
	Calculation: 44100 / 44100 = 1.00 seconds

	**要件**:
	1. ex28_bin_8bのコードに追加
	2. fmtチャンクの次（位置36）からdataチャンクヘッダーを読む
	3. データサイズからサンプル数を計算
	4. サンプル数から音声の長さ（秒）を計算
	5. 計算過程を表示
	*/

	printf("=== data Chunk ===\n");
	printf("Data size: %u\n", data.chunk_size);
	printf("\n");


	uint16_t	HowManySample = data.chunk_size / (fmt.bit_depth / 8 * fmt.channel_num);

	printf("=== Sample Count Calculation ===\n");
	printf(" - 何回サンプリングしたか？ \n");
	printf("Formula: data.chunk_size / (fmt.channel_num * fmt.bit_depth)\n");
	printf("Calculation: %u / (%u / %u)\n", data.chunk_size, fmt.channel_num, fmt.bit_depth);
	printf("Result: %u\n", HowManySample);
	printf("\n");

	uint16_t	Duration = data.chunk_size / ((fmt.bit_depth / 8 * fmt.channel_num) * fmt.sample_rate);

	printf("=== Duration Calculation ===\n");
	printf(" - 何秒サンプリングしたか？（何秒の音声データか？）\n");
	printf("Formula: data.chunk_size / ((fmt.bit_depth * fmt.channel_num) * fmt.sample_rate)\n");
	printf("Result: %u\n", Duration);

	fclose(fp);
	return 0;

	// 全体の量 / 一秒の量みたいなイメージ
}
