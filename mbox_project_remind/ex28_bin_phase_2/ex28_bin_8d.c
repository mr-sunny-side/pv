#include <stdio.h>
#include <stdint.h>
#include <string.h>

/*
	12-27:	- フィードバック.mdを読む
		- 複雑で意地の悪いwavファイルを作ってテスト

	## Code設計

	- fmt, dataが一回ずつ見つかるまでループ
		- fmtが見つかったらカウント
		 ※ fmtが用意している構造体より大きい場合、残りをスキップ
		- dataが見つかったらカウント
		 ※ データサイズ情報だけコピーして保存

		- 最後にカウントを確認してprintf

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
} FmtHeader;

#pragma pack(pop)

int	process_fread(FILE *fp, TmpChunk *tmp, FmtHeader *fmt, int *fmt_count, int *data_count, int *data_size) {

	if (fread(tmp, sizeof(*tmp), 1, fp) != 1) {
		fprintf(stderr, "fread/main: returned error\n");
		return 1;
	}

	if (memcmp(tmp->chunk_id, "fmt ", 4) == 0) {
		fseek(fp, -sizeof(*tmp), SEEK_CUR);				// 見つけたらfmtチャンクの先頭に戻り、fmt構造体に読み込む
		if (fread(fmt, sizeof(*fmt), 1, fp) != 1)
			return 1;
		*fmt_count = 1;

		size_t	fmt_data_size = sizeof(*fmt) - 8;			// chunk_sizeに記録されるのは「idとsizeデータ以外」なのでその分マイナス
		if (tmp->chunk_size > fmt_data_size) 				// fmtチャンクが想定より大きかった場合、残りを飛ばす
			fseek(fp, (tmp->chunk_size - fmt_data_size), SEEK_CUR);
	} else if (memcmp(tmp->chunk_id, "data", 4) == 0) {
		*data_size = tmp->chunk_size;
		*data_count = 1;
	} else {
		fseek(fp, tmp->chunk_size, SEEK_CUR);
		fprintf(stderr, "Unknown chunk is skiped\n");
	}

	return 0;

}

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

	if (memcmp(riff.chunk_id, "RIFF", 4) != 0 ||
		memcmp(riff.format, "WAVE", 4) != 0) {

		fprintf(stderr, "This file is not WAV\n");
		fclose(fp);
		return -1;
	}

	TmpChunk	tmp;
	FmtHeader	fmt;
	int		fmt_count = 0;
	int		data_count = 0;
	int		data_size = 0;
	while (!fmt_count || !data_count) {
		if (process_fread(fp, &tmp, &fmt, &fmt_count, &data_count, &data_size) != 0) {
			fprintf(stderr, "process_fread: returned error\n");
			fclose(fp);
			return 1;
		}
		if (data_count)
			break;
	}

	if (!fmt_count || !data_count) {
		fprintf(stderr, "Missing fmt or data chunk\n");
		fclose(fp);
		return 1;
	}

	/*
	=== Scanning chunks ===
	Found chunk: fmt  (size: 16 bytes)
	Found chunk: data (size: 88200 bytes)

	=== WAV File Information ===
	Audio format: 1
	Channels: 1
	Sample rate: 44100 Hz
	Bits per sample: 16
	Data size: 88200 bytes
	Duration: 1.00 seconds
	*/

	printf("=== Scanning Chunks ===\n");
	printf("Found chunk: fmt  (size: %u bytes)\n", fmt.chunk_size);
	printf("Found chunk: data (size: %u bytes)\n", data_size);
	printf("\n");

	uint16_t	bit_per_sample = fmt.bit_depth * fmt.channel_num;	// サンプルごとにbitは16, 24, 64とか2桁のintなので、uint16_tでok
	printf("=== WAV File Information ===\n");
	printf("Audio format: %u\n", fmt.audio_format);
	printf("Channels: %u\n", fmt.channel_num);
	printf("Sample rate: %u Hz\n", fmt.sample_rate);
	printf("Bits per sample: %u\n", bit_per_sample);
	printf("Data size: %u bytes\n", data_size);

	float	duration = tmp.chunk_size / ((fmt.bit_depth / 8 * fmt.channel_num) * fmt.sample_rate);
	printf("Duration: %.2f seconds\n", duration);

	fclose(fp);
	return 0;
}
