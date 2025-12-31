#include <stdio.h>
#include <stdint.h>
#include <string.h>

// 前回の復習
// 1. 無限ループを避けるため、feof()を利用
// 2. 不等号は < の方向で統一
// 3. windows_start.wav(16bit PCM)を想定して書く

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

	if (fread(tmp, sizeof(TmpHeader), 1, fp) != 1) {
		fprintf(stderr, "ERROR fread/process_read: Cannot read file\n");
		return -1;
	}

	if (memcmp(tmp->chunk_id, "fmt ", 4) == 0) {
		fprintf(stderr, "\nprocess_read: fmt chunk detected\n");
		if (fseek(fp, -sizeof(TmpHeader), SEEK_CUR) != 0) {
			fprintf(stderr, "ERROR fseek/process_read: Cannot move to start of fmt chunk\n");
			return -1;
		}
		fprintf(stderr, "process_read: moved to start of fmt chunk\n");

		if (fread(fmt, sizeof(FmtChunk), 1, fp) != 1) {
			fprintf(stderr, "ERROR fread/process_read: Cannot read fmt chunk\n");
			return -1;
		}
		fprintf(stderr, "process_read: fmt chunk is loaded\n");

		uint32_t	skip_size = fmt->chunk_size - (uint32_t)sizeof(FmtChunk);
		if (sizeof(FmtChunk) < fmt->chunk_size) {
			if (fseek(fp, skip_size, SEEK_CUR) != 0) {
				fprintf(stderr, "ERROR fseek/process_read: Cannot skip remaining fmt data\n");
				return -1;
			}
			fprintf(stderr, "process_read: Remaining fmt data is skipped\n");

		}

		*is_fmt = 1;

	} else if (memcmp(tmp->chunk_id, "data", 4) == 0) {
		fprintf(stderr, "\nprocess_read: data chunk detected\n");
		*data_size = tmp->chunk_size;
		*data_offset = ftell(fp);
		fprintf(stderr, "data_size: %u\n", *data_size);
		fprintf(stderr, "data_offset: %ld\n", *data_offset);
	} else {
		fprintf(stderr, "\nprocess_read: Unknown chunk detected [%.4s]\n", tmp->chunk_id);
		if (fseek(fp, tmp->chunk_size, SEEK_CUR) != 0) {
			fprintf(stderr, "ERROR fseek/process_read: Cannot skip Unknown chunk [%.4s]\n", tmp->chunk_id);
		}
		fprintf(stderr, "process_read: Unknown chunk is skipped [%.4s]\n", tmp->chunk_id);
	}

	return 0;
}

int	main(int argc, char **argv) {

	if (argc != 2) {
		fprintf(stderr, "ERROR main: Argument error\n");
		fprintf(stderr, "Usage: [This file] [.wav]\n");
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
		goto close_error;
	}

	if (memcmp(riff.chunk_id, "RIFF", 4) != 0 ||
		memcmp(riff.format, "WAVE", 4) != 0) {
		fprintf(stderr, "ERROR memcmp/main: This file is not WAV");
		goto close_error;
	}
	fprintf(stderr, "\nmain: This file is WAV\n");

	TmpHeader	tmp = {0};
	FmtChunk	fmt = {0};
	int		is_fmt = 0;
	uint32_t	data_size = 0;
	long		data_offset = 0;
	//int	process_read(FILE *fp, TmpHeader *tmp, FmtChunk *fmt, int *is_fmt, uint32_t *data_size, long *data_offset) {
	while (!is_fmt || !data_size) {
		if (process_read(fp, &tmp, &fmt, &is_fmt, &data_size, &data_offset) == -1) {
			fprintf(stderr, "ERROR process_read/main: returned error\n");
			goto close_error;
		}
		if (feof(fp))
			break;
	}

	if (!is_fmt || !data_size) {
		fprintf(stderr, "ERROR process_read/main: Cannot find fmt chunk or data chunk\n");
		goto close_error;
	}

	if (fmt.audio_format != 1 || fmt.bit_depth != 16) {
		fprintf(stderr, "ERROR main: This file is not 16bit PCM format\n");
		goto close_error;
	}
	fprintf(stderr, "\nmain: This file is 16bit PCM format\n");

	// fmtチャンクとdataヘッダーの抽出、検証は完了
	// 最大振幅の走査

	fclose(fp);
	return 0;

	close_error:
		fclose(fp);
		return -1;
}
