#include <stdio.h>
#include <stdint.h>
#include <string.h>

#define MAX_NUM 50

// 12-31: Claudeの提案を読む

// 前回の復習
// 1. 無限ループを避けるため、EOFで終了するコードを書く。またはマクロで定義する
// 2. 不等号は < の方向で統一
// 3. windows_start.wavでもテスト

// Code設計
// - ブロックアラインごとにサンプルを走査し、最大振幅を見つける
//
// - 各サンプルは音の振幅を示す。最大値は-32768から32767
// - ブロックアラインごとに意味を成す

#pragma pack(push, 1)

typedef	struct {
	char		chunk_id[4];
	uint32_t	chunk_size;
} TmpHeader;

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

int	process_read(FILE *fp, TmpHeader *tmp, FmtChunk *fmt, int *is_fmt, uint32_t *data_size, long *data_offset) {

	if (fread(tmp, sizeof(*tmp), 1, fp) != 1) {
		fprintf(stderr, "ERROR fread/process_read: Cannot read TmpHeader\n");
		return -1;
	}

	// fmtチャンクの読み込み
	if (memcmp(tmp->chunk_id, "fmt ", 4) == 0) {
		fprintf(stderr, "\nprocess_read: fmt chunk detected\n");
		fprintf(stderr, "chunk_id: %.4s\n", fmt->chunk_id);
		// fmtチャンクを見つけたら、その先頭に移動
		if (fseek(fp, -sizeof(*tmp), SEEK_CUR) != 0) {
			fprintf(stderr, "ERROR fseek/process_read: Cannot move to start of fmt chunk");
			return -1;
		}

		// freadで読み込み
		if (fread(fmt, sizeof(*fmt), 1, fp) != 0) {
			fprintf(stderr, "ERROR fread/process_read: Cannot read FmtChunk\n");
			return -1;
		}

		uint32_t	skip_size = fmt->chunk_size - (uint32_t)(sizeof(*fmt));
		if (sizeof(*fmt) < fmt->chunk_size) {
			if (fseek(fp, skip_size, SEEK_CUR)) {
				fprintf(stderr, "ERROR fseek/main Cannot move to end of fmt chunk\n");
				return -1;

			}
			fprintf(stderr, "process_read: Remaining data of fmt chunk is skipped\n");
			fprintf(stderr, "fmt chunk_size: %u\n", fmt->chunk_size);
			fprintf(stderr, "skip size: %u\n", skip_size);
		}
		fprintf(stderr, "process_read: FmtChunk is loaded\n");
		*is_fmt = 1;
	// dataチャンクの読み込み
	} else if (memcmp(tmp->chunk_id, "data", 4) == 0) {
		fprintf(stderr, "\nprocess_read: data chunk detected\n");
		*data_size = tmp->chunk_size;
		*data_offset = ftell(fp);
		fprintf(stderr, "data_size: %u\n", *data_size);
		fprintf(stderr, "data_offset, %ld\n", *data_offset);
	// 未定義のチャンク
	} else {
		fprintf(stderr, "\nprocess_read: Unknown chunk detected\n");
		fprintf(stderr, "chunk_id: %.4s", tmp->chunk_id);
		if (fseek(fp, tmp->chunk_size, SEEK_CUR)) {
			fprintf(stderr, "ERROR fseek/process_read: Cannot move to end of unknown chunk\n");
			return -1;
		}
		fprintf(stderr, "Unknown chunk is skipped: %.4s\n", tmp->chunk_id);
	}

	return 0;


}

int	main(int argc, char **argv) {

	if (argc != 2) {
		fprintf(stderr, "ERROR main: Argument error\n");
		return -1;
	}

	const char	*file_name = argv[1];
	FILE		*fp = fopen(file_name, "rb");
	if (fp == NULL) {
		fprintf(stderr, "ERROR main: Cannot Open %s", file_name);
		return -1;
	}

	RiffHeader	riff = {0};
	if (fread(&riff, sizeof(riff), 1, fp) != 1) {
		fprintf(stderr, "ERROR fread/main: Cannot read RIFF header\n");
		return -1;
	}

	if (memcmp(riff.chunk_id, "RIFF", 4) != 0 ||
		memcmp(riff.format, "WAVE", 4) != 0) {

		fprintf(stderr, "ERROR memcmp/main: This file is not WAV\n");
		fprintf(stderr, "chunk_id: %.4s\nformat: %.4s\n", riff.chunk_id, riff.format);
		fclose(fp);
		return -1;
	}
	fprintf(stderr, "main: This file is WAV\n");

	TmpHeader	tmp = {0};
	FmtChunk	fmt = {0};
	int		i = 0;
	int		is_fmt = 0;
	uint32_t	data_size = 0;
	long		data_offset = 0;

	// チャンクの読み込み
	// FILE *fp, TmpHeader *tmp, FmtChunk *fmt, int *is_fmt, uint32_t *data_size, long *data_offset
	while ((!is_fmt || !data_size) && i < MAX_NUM) {
		if (process_read(fp, &tmp, &fmt, &is_fmt, &data_size, &data_offset) == -1) {
			fprintf(stderr, "ERROR process_read/main: returned error\n");
			return -1;
		}
		i++;
	}

	// 最大振幅の走査
	// 1. データオフセットに移動
	if (fseek(fp, data_offset, SEEK_SET) != 0) {
		fprintf(stderr, "ERROR fread/main: Cannot move to data_offset\n");
		fprintf(stderr, "data_offset: %ld\n", data_offset);
		return -1;
	}


}
