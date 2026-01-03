#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>

/*
	dataチャンクの特定位置のサンプルを返す
	- dataチャンクまで読み取る
	- サンプリング位置を記録
	- そこからブロックアライン(一回のサンプルごとのデータ量) * 特定位置で計算

	12-28: errorコード
	```bash
	$C_FILE/ex28_bin_10a_file $BIN_FILE/sample2_extended.wav 10
	process_read: Cannot read the file
	process_read/main: returned error
	fmt: 1
	data_size: 0
	data_offset: 0
	```
*/

#pragma pack(push,1)

typedef struct {
	char		chunk_id[4];
	uint32_t	chunk_size;
	char		format[4];
} RiffHeader;

typedef struct {
	char		chunk_id[4];
	uint32_t	chunk_size;
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

int	process_read(FILE *fp, FmtChunk *fmt, TmpChunk *tmp, int *is_fmt, int *data_size, long *data_offset) {

	if (fread(tmp, sizeof(*tmp), 1, fp) != 1) {
		fprintf(stderr, "process_read: Cannot read the file\n");
		return 1;
	}

	if (memcmp(tmp->chunk_id, "fmt ", 4) == 0) {
		fseek(fp, -sizeof(*tmp), SEEK_CUR);
		if (fread(fmt, sizeof(*fmt), 1, fp) != 1) {
			fprintf(stderr, "process_read: Cannot read fmt chunk\n");
			return 1;
		}
		*is_fmt += 1;

		int	skip_num = (int)(fmt->chunk_size - (uint32_t)(sizeof(FmtChunk) - 8));	//型の不整合(特に符号無しあり)によるコンパイルエラーに注意
		if (fmt->chunk_size > (uint32_t)(sizeof(FmtChunk) - 8)){		// チャンクサイズはIDとサイズ情報(8bytes)を引いた数でなければならない
			fseek(fp, skip_num, SEEK_CUR);
		}

	} else if (memcmp(tmp->chunk_id, "data", 4) == 0) {
		*data_size = (int)tmp->chunk_size;
		*data_offset = ftell(fp);
	} else {
		fseek(fp, (int)tmp->chunk_size, SEEK_CUR);
		fprintf(stderr, "Unknown chunk is skipped: %.4s\n", tmp->chunk_id);
	}

	return 0;
}

int	search_bin(FILE *fp, FmtChunk *fmt, long data_offset, int need_offset) {
	//bin_dataが取得できない場合は-1

	long	bit_per_sample = fmt->bit_depth * fmt->channel_num;
	long	result_offset = data_offset + ((bit_per_sample / 8) * need_offset);

	fseek(fp, result_offset, SEEK_SET);
	int	bin_data = 0;
	if (fread(&bin_data, (bit_per_sample / 8), 1, fp) != 1) {
		fprintf(stderr, "search_bin: Cannot read a bin data\n");
		return -1;
	}

	return bin_data;	// errorを != 0にすると、せっかく出力出来たデータもエラー扱いになってしまう
}

int	main(int argc, char **argv) {

	if (argc != 3) {
		fprintf(stderr, "Argument error\n");
		return -1;
	}

	const char	*file_name = argv[1];
	FILE		*fp = fopen(file_name, "rb");
	if (fp == NULL) {
		fprintf(stderr, "main: Cannot open %s\n", file_name);
		return 1;
	}

	RiffHeader	riff;
	if (fread(&riff, sizeof(riff), 1, fp) != 1) {
		fprintf(stderr, "main: Cannot read RIFF header\n");
		fclose(fp);
		return 1;
	}

	if (memcmp(riff.chunk_id, "RIFF", 4) != 0 ||
		memcmp(riff.format , "WAVE", 4) != 0) {

		fprintf(stderr, "main: This file is not WAV\n");
		fclose(fp);
		return -1;
	}

	TmpChunk	tmp = {0};
	FmtChunk	fmt = {0};
	int		is_fmt = 0;
	int		data_size = 0;
	long		data_offset = 0;	// あくまでオフセットなのでポインタではない
	int		result = 0;
	while (!is_fmt || !data_size || !data_offset) {
		result = process_read(fp, &fmt, &tmp, &is_fmt, &data_size, &data_offset);
		if (result != 0) {
			fprintf(stderr, "process_read/main: returned error\n");
			fprintf(stderr, "fmt: %d\ndata_size: %d\ndata_offset: %ld\n", is_fmt, data_size, data_offset);
			fclose(fp);
			return result;
		}
	}

	// チャンクを読み取れないままEOFになった場合、process_readのfreadがエラーを吐くが念のため
	if (!is_fmt || !data_size || !data_offset) {
		fprintf(stderr, "main: Cannot find fmt chunk, data_size, or data_offset\n");
		fclose(fp);
		return 1;
	}

	const int	need_offset = atoi(argv[2]);
	int		bin_data = 0;
	bin_data = search_bin(fp, &fmt, data_offset, need_offset);
	if (bin_data == -1) {
		fprintf(stderr, "search_bin/main: returned error\n");
		fclose(fp);
		return 1;
	}

	printf("=== Result ===\n");
	printf("Bin data: %0x\n", bin_data);
	printf("\n");

	fclose(fp);
	return 0;
}
