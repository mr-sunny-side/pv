#include <stdio.h>
#include <stdint.h>
#include <string.h>

/*
	**要件**:
	1. コマンドライン引数で開始時刻と終了時刻を指定
	2. その範囲のサンプルを表示
	3. 最大表示数を制限（例: 20サンプル）
*/

#pragma pack(push, 1)

typedef	struct {
	char		chunk_id[4];
	uint32_t	chunk_size;
	char		format[4];
} RiffHeader;

/*
	位置12-15:  "fmt " (チャンクID、スペース含む)
	位置16-19:  チャンクサイズ（通常16）
	位置20-21:  オーディオフォーマット（1=PCM）
	位置22-23:  チャンネル数（1=モノラル、2=ステレオ）
	位置24-27:  サンプリングレート（Hz）
	位置28-31:  バイトレート
	位置32-33:  ブロックアライン
	位置34-35:  ビット深度
*/

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

typedef	struct {
	char		chunk_id[4];
	uint32_t	chunk_size;
} TmpHeader;

#pragma pack(pop)



int	process_read(FILE *fp, FmtChunk *fmt, TmpHeader *tmp, uint32_t *data_size, long *data_offset) {

	// tmpへの読み込み
	if (fread(tmp, sizeof(*tmp), 1, fp) != 1) {
		fprintf(stderr, "ERROR fread/process_read: Cannot read file\n");
		return -1;
	}

	// fmt, dataチャンクかどうか検証
	if (memcmp(tmp->chunk_id, "fmt ", 4) == 0) {
		//fmtチャンク情報の読み込み
		fprintf(stderr, "\nmemcmp/process_read: fmt chunk detected\n");
		// 一度fmtチャンクの先頭へ移動
		if (fseek(fp, -8, SEEK_CUR) != 0)  {
			fprintf(stderr, "ERROR fseek/process_read: Cannot seek start of fmt\n");
			return -1;
		}

		// 先頭に戻った上でfmt構造体へ読み込み
		if(fread(fmt, sizeof(*fmt), 1 ,fp) != 1) {
			fprintf(stderr, "ERROR fread/process_read: Cannot read fmt chunk\n");
			return -1;
		}

		// fmtチャンクが想定より大きかった場合スキップ
		if (fmt->chunk_size > sizeof(*fmt) - 8) {
			long	skip_num = (fmt->chunk_size - (sizeof(*fmt) - 8));
			if (fseek(fp, skip_num, SEEK_CUR) != 0) {
				fprintf(stderr, "ERROR fseek/process_read: Cannot skip the remaining data in fmt chunk\n");
				return -1;
			}
			fprintf(stderr, "fseek/process_read: The remaining data in fmt chunk is skipped\n");
			fprintf(stderr, "fmt chunk size: %u\n", fmt->chunk_size);
			fprintf(stderr, "skipped size: %ld\n", skip_num);
		}
		fprintf(stderr, "process_read: fmt chunk is loaded\n");
	} else if (memcmp(tmp->chunk_id, "data", 4) == 0) {
		// dataチャンク情報の読み込み
		fprintf(stderr, "\nmemcmp/process_read: data chunk detected\n");

		*data_size = tmp->chunk_size;
		*data_offset = ftell(fp);
		fprintf(stderr, "process_read: data chunk is loaded\n");
		fprintf(stderr, "data_size: %u\n", data_size);
		fprintf(stderr, "data_offset %ld\n");

		// 残りのサンプルデータを飛ばして次のチャンクに飛ぶ
		if (fseek(fp, tmp->chunk_size, SEEK_CUR) != 0) {
			fprintf(stderr, "fseek/process_read: Cannot skip the sample_data in data chunk\n");
			return -1;
		}
		fprintf(stderr, "process_read: the sample_data is skipped\n");
	} else {
		// 未知のチャンクをスキップ
		fprintf(stderr, "\nprocess_read: Unkown chunk is detected: %.4s\n", tmp->chunk_id);
		if (fseek(fp, tmp->chunk_size, SEEK_CUR) != 0) {
			fprintf(stderr, "ERROR fseek/process_read: Cannot skip unknown chunk\n");
			return -1;
		}
		fprintf(stderr, "process_read: Unknown chunk is skipped: %.4s\n", tmp->chunk_id);
	}

	return 0;
}

int	*get_bin(FILE fp, const FmtChunk *fmt, uint32_t data_size, long data_offset, float start_time ,float end_time) {
	// 学習用に敢えて計算
	uint32_t	bytes_per_sample = (fmt->bit_depth / 8) *fmt->channel_num;
	uint32_t	bytes_per_second = bytes_per_sample * fmt->sample_rate;
	if (fmt->byte_rate != bytes_per_second) {
		fprintf(stderr, "ERROR get_bin: bytes_per_second is incorrect\n");
		return -1;
	}
	fprintf(stderr, "\nget_bin: bytes_per_sample formula is correct\n");

	if (end_time > start_time) {
		fprintf(stderr, "ERROR get_bin: Argument is invalid\n");
		fprintf(stderr, "start_time: %.3f end_time: %.3f\n", start_time, end_time);
		return -1;
	}

	// ループしてすべてのバイナリデータを取得
	// ※ カウントはidxで行っているので注意
	long	start_offset = data_offset + (long)((float)fmt->byte_rate * start_time);
	long	end_offset = data_offset + (long)((float)fmt->byte_rate * end_time);
	int	howmany_bins = (int)end_time - (int)start_time;
	int	*result_array = malloc(sizeof(int) * (howmany_bins + 1));
		//howmany_binsはidxなので、実際に読むバイナリ数は+1
	for (int i = 0; i <= howmany_bins; i++) {
		if (fread(result_array[i], bytes_per_sample, ))

	}

}

int	main(int argc, char **argv) {

	if (argc != 4) {
		fprintf(stderr ,"ERROR /main: Argument error\n");
		return -1;
	}

	const char	*file_name = argv[1];
	FILE		*fp = fopen(file_name, "rb");
	if (fp == NULL) {
		fprintf(stderr, "ERROR fopen/main: Cannot open %s\n", file_name);
		return -1;
	}

	RiffHeader	riff;
	if (fread(&riff, sizeof(riff), 1, fp) != 1) {
		fprintf(stderr, "ERROR fread/main: returned error\n");
		fclose(fp);
		return -1;
	}

	if (memcmp(riff.chunk_id, "RIFF", 4) != 0 ||
		memcmp(riff.format, "WAVE", 4) != 0) {

		fprintf(stderr, "ERROR memcmp/main: This file is not WAV\n");
		fclose(fp);
		return -1;
	}

	FmtChunk	fmt = {0};
	TmpHeader	tmp = {0};
	uint32_t	data_size = 0;
	long		data_offset = 0;
	int		result = process_read(fp, &fmt, &tmp, &data_size, &data_offset);
	if (result == -1) {
		fprintf(stderr, "ERROR process_read/main: returned error\n");
		return -1;
	}

	float	start_time = atof(argv[2]);
	float	end_time = atof(argv[3]);

}
