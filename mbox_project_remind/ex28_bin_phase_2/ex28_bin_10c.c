#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>

/*
	**要件**:
	1. コマンドライン引数で開始時刻と終了時刻を指定
	2. その範囲のサンプルを表示
	3. 最大表示数を制限（例: 20サンプル）

	12-30: reviewを読む 備忘録を参照
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



int	process_read(FILE *fp, FmtChunk *fmt, TmpHeader *tmp, int *is_fmt, uint32_t *data_size, long *data_offset) {

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
		*is_fmt = 1;
		fprintf(stderr, "process_read: fmt chunk is loaded\n");

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
	} else if (memcmp(tmp->chunk_id, "data", 4) == 0) {
		// dataチャンク情報の読み込み
		fprintf(stderr, "\nmemcmp/process_read: data chunk detected\n");

		*data_size = tmp->chunk_size;
		*data_offset = ftell(fp);
		fprintf(stderr, "process_read: data chunk is loaded\n");
		fprintf(stderr, "data_size: %u\n", *data_size);
		fprintf(stderr, "data_offset %ld\n", *data_offset);

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

int	print_bin(FILE *fp, const FmtChunk *fmt, uint32_t data_size, long data_offset, float start_time, float end_time) {

	// 開始位置と終了位置の数値の整合性確認
	if (end_time < start_time) {
		fprintf(stderr, "ERROR print_bin Argument is invalid\n");
		fprintf(stderr, "start_time: %.3f end_time: %.3f\n", start_time, end_time);
		return -1;
	}

	uint32_t	bytes_per_sample = (fmt->bit_depth / 8) * fmt->channel_num;
	uint32_t	bytes_per_second = bytes_per_sample * fmt->sample_rate;		// 学習用に敢えて計算
	float		duration = (float)data_size / (float)bytes_per_second;
	fprintf(stderr, "\nprint_bin: duration(%.3f) = data_size(%.3f) / bytes_per_second(%.3f byte_rate:(%u))",
		duration, (float)data_size, (float)bytes_per_second, fmt->byte_rate);
	// 終了位置の秒数とファイルの持っているデータの秒数の整合性確認
	if (duration < end_time) {
		fprintf(stderr, "ERROR print_bin: Argument is invalid\n");
		fprintf(stderr, "Duration: %.3f end_time: %.3f\n", duration, end_time);
		return -1;
	}

	if (fmt->byte_rate != bytes_per_second) {					//学習用の計算の正誤確認
		fprintf(stderr, "ERROR print_bin bytes_per_second is incorrect\n");
		return -1;
	}
	fprintf(stderr, "\nprint_bin bytes_per_sample formula is correct\n");

	long	start_offset = data_offset + (long)((float)fmt->byte_rate * start_time);
	long	end_offset = data_offset + (long)((float)fmt->byte_rate * end_time);
	fprintf(stderr, "\nstart_offset(%ld): data_offset(%ld) + (fmt->byte_rate(%u) * start_time(%.3f))\n",
			start_offset, data_offset, fmt->byte_rate, start_time);
	fprintf(stderr, "end_offset(%ld): data_offset(%ld) + (fmt->byte_rate(%u) * end_time(%.3f))",
		end_offset, data_offset, fmt->byte_rate, end_time);

	int		i = 0;					// 一行16個のバイナリを表示するためのidx
	long		print_offset = start_offset;		// print_offsetは今読んでいるoffsetを左に表示するために使う
	unsigned char	byte_sample = 0;			// hexdumpと同じく1バイトずつ出力するので、すべての環境で1バイトのcharを使う

	if (fseek(fp, start_offset, SEEK_SET) != 0) {			// start_offsetに移動
		fprintf(stderr, "ERROR fseek/print_bin Cannot seek data offset\n");
		return -1;
	}
	fprintf(stderr, "\nfseek/print_bin: seek start_offset: %ld\n\n", start_offset);


	// ループしてすべてのバイナリデータを取得
	// ※ offsetはidxなので条件式に注意
	// hexdump -Cと同じように出力
	while (end_offset > print_offset) {
		printf("%08lx ", print_offset); // 16進数のデータオフセットを左に表示
		i = 0;
		while (16 > i && end_offset > print_offset) {	// start(0)から読むので(end未満)、>で最後は含まないようにする
			/*
				1. サンプルごとにバイナリを取得
				2. printf
				3. i++, print_offset+=bytes_per_sample
			*/
			if (fread(&byte_sample, 1, 1, fp) != 1) {
				fprintf(stderr, "ERROR fread/print_bin: Cannot read sample data\n");
				return -1;
			}
			printf("%02x ", byte_sample);
			i++;
			print_offset++;
		}
		printf("\n");
	}

	return 0;
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
	int		is_fmt = 0;
	uint32_t	data_size = 0;
	long		data_offset = 0;
	while (!is_fmt || !data_size) {
		if (process_read(fp, &fmt, &tmp, &is_fmt, &data_size, &data_offset) == -1) {
			fprintf(stderr, "ERROR process_read/main: returned error\n");
			return -1;
		}
	}

	float	start_time = atof(argv[2]);
	float	end_time = atof(argv[3]);
	if (print_bin(fp, &fmt, data_size, data_offset, start_time, end_time) == -1) {
		fprintf(stderr, "ERROR print_bin/main: returned error");
		return -1;
	}

	fclose(fp);
	return 0;

}
