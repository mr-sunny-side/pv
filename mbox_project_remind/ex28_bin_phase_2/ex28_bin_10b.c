#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

/*
	12-28: エラー情報
	```bash
	NK-PC% $C_FILE/ex28_bin_10b_file $BIN_FILE/sample.wav 0.5
	Sample data offset: 44
	byte_rate formula is true
	fread/get_bin: Cannot read bin data
	*** stack smashing detected ***: terminated
	zsh: IOT instruction (core dumped)  $C_FILE/ex28_bin_10b_file $BIN_FILE/sample.wav 0.5
	```
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
	uint32_t	byte_rate;
	uint16_t	block_align;
	uint16_t	bit_depth;
} FmtHeader;

typedef	struct {
	char		chunk_id[4];
	uint32_t	chunk_size;
} TmpHeader;

#pragma pack(pop)

/*
	**必要な情報**:
	data_offset - サンプルが始まる先頭offset
	byte_rate - 一秒間に記録するbyte数

	**設計**
	1. riff, fmt, dataチャンクを全部読む
		1. 必要ない情報もあるが、fseekで読むより確実で後から追加で情報を持ってきやすい
	2. dataヘッダーに到達した時点でサンプルoffsetを記録
	3. サンプルoffset + バイトレート * 指定秒数でバイナリデータを取得
		3. 引数の.wavが持っているサイズより大きな秒数を指定されたら、エラーを返す

	**要件**:
	1. ex28_bin_10aを拡張
	2. コマンドライン引数で時刻（秒）を指定
	3. その時刻のサンプルを表示
*/

int	get_bin(FILE *fp, FmtHeader *fmt, int data_size, long data_offset, float need_second) {

	float	bit_per_sample = (float)(fmt->bit_depth * fmt->channel_num);
	float	bit_per_second = bit_per_sample * (float)fmt->sample_rate;
	if ((uint32_t)(bit_per_second / 8) == fmt->byte_rate)
		fprintf(stderr, "byte_rate formula is true\n");
	else {
		fprintf(stderr, "Error: byte_rate formula is invalid\n");
		return -1;
	}

	float	duration = (float)data_size / (bit_per_second / 8);
	if (duration < need_second) {
		fprintf(stderr, "get_bin: need_second is too big\n");
		return -1;
	}

	long	result_offset = data_offset + (long)((bit_per_second / 8) * need_second);	// 修正
	fseek(fp, result_offset, SEEK_SET);

	int	bin_data = 0;
	int	result_read = (int)(bit_per_sample / 8);
	if (fread(&bin_data, result_read, 1, fp) != 1) {	// 修正
		fprintf(stderr, "fread/get_bin: returned error\n");
		return 1;
	}

	return bin_data;
}

int	process_read(FILE *fp, TmpHeader *tmp, FmtHeader *fmt, int *is_fmt, int *data_size, long *data_offset) {

	if (fread(tmp, sizeof(*tmp), 1, fp) != 1) {
		fprintf(stderr, "fread/process_read: Cannot read the file\n");
		return 1;
	}

	if (memcmp(tmp->chunk_id, "fmt ", 4) == 0) {
		fseek(fp, -sizeof(*tmp), SEEK_CUR);
		if (fread(fmt, sizeof(*fmt), 1, fp) != 1) {
			fprintf(stderr, "fread/process_read: Cannot read fmt chunk\n");
			return 1;
		}
		*is_fmt += 1;

		int	skip_num = (int)(fmt->chunk_size - (uint32_t)(sizeof(*fmt) - 8));
		if (fmt->chunk_size > (uint32_t)(sizeof(*fmt) - 8)) {	// チャンクサイズはidとサイズデータを除いた値
			fseek(fp, skip_num, SEEK_CUR);
			fprintf(stderr, "Rest fmt chunk is skipped\n");
		}

	} else if (memcmp(tmp->chunk_id, "data", 4) == 0) {
		*data_offset = ftell(fp);
		*data_size = tmp->chunk_size;
		fprintf(stderr, "Sample data offset: %ld\n", *data_offset);
	} else {
		fseek(fp, tmp->chunk_size, SEEK_CUR);
		fprintf(stderr, "Unknown chunk is skipped: %.4s\n", tmp->chunk_id);
	}

	return 0;
}

int	main(int argc, char **argv) {
	if (argc != 3) {
		fprintf(stderr, "Argument error\n");
		fprintf(stderr, "Usage: [this file] [.wav] [need to know the data offset]\n");
		return -1;
	}

	const char	*file_name = argv[1];
	FILE		*fp = fopen(file_name, "rb");
	if (fp == NULL) {
		fprintf(stderr, "fopen/main: Cannot open %s\n", file_name);
		return 1;
	}

	RiffHeader	riff;
	if (fread(&riff, sizeof(riff), 1, fp) != 1) {
		fprintf(stderr, "fread/main: Cannot read RIFF header\n");
		fclose(fp);
		return 1;
	}

	if (memcmp(riff.chunk_id, "RIFF", 4) != 0 ||
		memcmp(riff.format, "WAVE", 4) != 0) {

		fprintf(stderr, "memcmp/main: This file is not WAV\n");
		fclose(fp);
		return -1;
	}

	FmtHeader	fmt = {0};
	TmpHeader	tmp = {0};
	int		is_fmt = 0;
	int		data_size = 0;
	long		data_offset = 0;
	int		result = 0;
	while (!is_fmt || !data_offset) {
		result = process_read(fp, &tmp, &fmt, &is_fmt, &data_size, &data_offset);
		if (result != 0) {
			fprintf(stderr, "process_read/main: returned error\n");
			return result;
		}
	}

	if (!is_fmt || !data_offset) {
		fprintf(stderr, "main: Cannot find fmt chunk or data offset\n");
		fclose(fp);
		return 1;
	}

	float	need_second = atof(argv[2]);		// 修正
	int	bin_data = get_bin(fp, &fmt, data_size, data_offset, need_second);
	if (bin_data == -1 || bin_data == 1) {
		fprintf(stderr, "get_bin/main: returned error\n");
		return result;
	}

	printf("=== Result ===\n");
	printf("bin: %d", bin_data);
	printf("\n");

	fclose(fp);
	return 0;
}
