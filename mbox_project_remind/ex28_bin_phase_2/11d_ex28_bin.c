#include <stdio.h>
#include <stdint.h>
#include <string.h>

// **目的**: 最大振幅、ゼロクロスを1回の走査で計算する(余裕があればRMS)
// 01-03: チャンク情報読み取りまで記述
//		- 最大振幅、ゼロクロスの操作記述から
//		- 16bitPCMでない場合、チャンク情報、durationなどを出力して終了する

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

int	process_read(FILE *fp, FmtChunk *fmt, TmpHeader *tmp, int *is_fmt, uint32_t *data_size, long *data_offset) {

	if (fread(tmp, sizeof(TmpHeader), 1, fp) != 1) {
		fprintf(stderr, "ERROR fread/process_read: Cannot read TmpHeader\n");
		return -1;
	}


	// fmt chunk読み込み
	if (memcmp(tmp->chunk_id, "fmt ", 4) == 0) {
		fprintf(stderr, "process_read: fmt chunk detected\n");
		// fmt chunk先頭へ移動
		if (fseek(fp, -sizeof(TmpHeader), SEEK_CUR) != 0) {
			fprintf(stderr, "ERROR fseek/process_read: Cannot move to start of fmt chunk\n");
			return -1;
		}

		// fmt chunkを読み込み
		if (fread(fmt, sizeof(FmtChunk), 1, fp) != 1) {
			fprintf(stderr, "ERROR fread/process_read: Cannot read fmt chunk\n");
			return -1;
		}
		*is_fmt = 1;

		// 16byte以上のfmt chunkの残りをスキップ
		uint32_t	fmt_size = (uint32_t)sizeof(FmtChunk) - 8;
		if (fmt_size < fmt->chunk_size) {
			uint32_t	skip_size = fmt->chunk_size - fmt_size;
			if (fseek(fp, skip_size, SEEK_CUR) != 0) {
				fprintf(stderr, "ERROR fseek/process_read: Cannot skip rest of fmt chunk\n");
				return -1;
			}
			fprintf(stderr, "process_read: Rest of fmt chunk is skipped\n");
			fprintf(stderr, " - fmt chunk size: %u\n", fmt->chunk_size);
			fprintf(stderr, " - skip_size: %u\n", skip_size);
		}
		fprintf(stderr, "process_read: fmt chunk lorded\n");
	// data header読み込み
	} else if (memcmp(tmp->chunk_id, "data", 4) == 0) {
		fprintf(stderr, "process_read: data header detected\n");

		*data_size = tmp->chunk_size;
		*data_offset = ftell(fp);
		fprintf(stderr, " - data_size: %u\n", *data_size);
		fprintf(stderr, " - data_offset: %ld\n", *data_offset);
	// 未定義チャンクをスキップ
	} else {
		if (fseek(fp, tmp->chunk_size, SEEK_CUR) != 0) {
			fprintf(stderr, "ERROR fseek/processs_read: Cannot skip unknown chunk\n");
			return -1;
		}
		fprintf(stderr, "process_read: Unknown chunk is skipped [%.4s]\n", tmp->chunk_id);
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
		fprintf(stderr, "ERROR fopen/main: Cannot open %s\n", file_name);
		return -1;
	}

	RiffHeader	riff = {0};
	if (fread(&riff, sizeof(RiffHeader), 1, fp) != 1) {
		fprintf(stderr, "ERROR fread/main: Cannot read RIFF header\n");
		goto clean_error;
	}

	if (memcmp(riff.chunk_id, "RIFF", 4) != 0 ||
		memcmp(riff.format, "WAVE", 4) != 0) {
		fprintf(stderr, "ERROR main: This file is not WAV\n");
		goto clean_error;
	}
	fprintf(stderr, "main: This file is WAV\n");

	// fmt, data chunkの読み込みループ
	TmpHeader	tmp = {0};
	FmtChunk	fmt = {0};
	int			is_fmt = 0;
	uint32_t	data_size = 0;
	long		data_offset = 0;
	while (!is_fmt || !data_size || !data_offset) {
		if (feof(fp))
			break;
		if (process_read(fp, &fmt, &tmp, &is_fmt, &data_size, &data_offset) == -1) {
			fprintf(stderr, "ERROR process_read/main: returned error\n");
			goto clean_error;
		}
	}

	if (!is_fmt || !data_size || !data_offset) {
		fprintf(stderr, "ERROR main: Cannot find fmt chunk or data chunk\n");
		fprintf(stderr, "is_fmt: %d\n", is_fmt);
		fprintf(stderr, "data_size: %u\n", data_size);
		fprintf(stderr, "data_offset: %ld\n", data_offset);
		goto clean_error;
	}

	fclose(fp);
	return 0;

	clean_error:
		fclose(fp);
		return -1;

}
