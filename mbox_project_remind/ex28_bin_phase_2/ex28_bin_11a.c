#include <stdio.h>
#include <stdint.h>
#include <string.h>

#define MAX_NUM 100

// 12-31: windows_start.wav (PCM, stereo) 専用に構築した。
//	ロジックエラーを修正
//	 - 絶対値計算の簡略化

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
		fprintf(stderr, "chunk_id: %.4s\n", tmp->chunk_id);
		// fmtチャンクを見つけたら、その先頭に移動
		if (fseek(fp, -8, SEEK_CUR) != 0) {
			fprintf(stderr, "ERROR fseek/process_read: Cannot move to start of fmt chunk");
			return -1;
		}

		// freadで読み込み
		if (fread(fmt, sizeof(*fmt), 1, fp) != 1) {
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
		fprintf(stderr, "chunk_id: %.4s\n", tmp->chunk_id);
		if (fseek(fp, tmp->chunk_size, SEEK_CUR)) {
			fprintf(stderr, "ERROR fseek/process_read: Cannot move to end of unknown chunk\n");
			return -1;
		}
		fprintf(stderr, "Unknown chunk is skipped: %.4s\n", tmp->chunk_id);
	}

	return 0;
}


void	get_max_stereo(uint16_t bits_per_sample, int *stereo_sample, int *max_sample) {
	// 16ビットPCMなら符号付き16ビット整数、つまり-32768から32767の範囲の値です。
	// 8ビットPCMなら符号なし8ビット整数で0から255の範囲です。
	// 32ビット浮動小数点PCMなら-1.0から1.0の範囲の浮動小数点数です。

	// 8bit PCMの場合128からの絶対値に変換し、振幅の計算をしやすくする。
	if (bits_per_sample == 8) {
		if (stereo_sample[0] == 128)
			stereo_sample[0] = 0;
		else if (stereo_sample[0] < 128)
			stereo_sample[0] = 128 - stereo_sample[0];
		else
			stereo_sample[0] = stereo_sample[0] - 128;

		if (stereo_sample[1] == 128)
			stereo_sample[1] = 0;
		else if (stereo_sample[1] < 128)
			stereo_sample[1] = 128 - stereo_sample[1];
		else
			stereo_sample[1] = stereo_sample[1] - 128;
	}

	// 8bit PCM以外のPCMの場合、すべての負の数を絶対値に変換
	if (stereo_sample[0] < 0)
		stereo_sample[0] *= -1;
	if (stereo_sample[1] < 0)
		stereo_sample[1] *= -1;

	// 最大値の検証
	if (max_sample[0] < stereo_sample[0])
		max_sample[0] = stereo_sample[0];
	if (max_sample[1] < stereo_sample[1])
		max_sample[1] = stereo_sample[1];
}

// byte_sampleとmax_sampleを比較して、振幅の最大値を更新する関数

// 最大振幅を見つけるループ関数(stereo)
int	process_get_stereo(FILE *fp, const FmtChunk *fmt, int *max_sample) {

	int		stereo_sample[2] = {0, 0};
	int16_t		tmp_sample = 0;			// windows_start.wavは左右それぞれ16ビットなので、先ずここにいれる
							// 16ビットPCMは符号付の振幅表現なのでint16_t
	uint16_t	bits_per_sample = fmt->bit_depth * fmt->channel_num;

	while (1) {
		if (fread(&tmp_sample, fmt->bit_depth / 8, 1, fp) != 1) {	// bit_depthは左右のサンプルごとのサイズ（ただしbit単位なので注意）
			if (feof(fp))	// fread == errorの際は、ファイル終端 or errorなので、終端かチェックしてループを抜ける
				break;
			fprintf(stderr, "ERROR fread/process_get_stereo: Cannot read stereo sample\n");
			return -1;
		}
		stereo_sample[0] = (int)tmp_sample;	// int型にそのまま読込むと、int型が32ビットで上位バイトが0000で解釈され (0x00001234)別の数字になってしまうので、
							// ここで明確にint型にキャストして数値解釈を守る

		if (fread(&tmp_sample, fmt->bit_depth / 8, 1, fp) != 1) {
			fprintf(stderr, "ERROR fread/process_get_stereo: Cannot read stereo sample\n");
			return -1;
			// ファイル終端が、片方だけ読み込めないケースはあり得ない
			// よってこっちのfread() == errorは本当にエラー
		}
		stereo_sample[1] = (int)tmp_sample;

		get_max_stereo(bits_per_sample, stereo_sample, max_sample);

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
			fclose(fp);
			return -1;
		}
		i++;
	}

	// PCM formatか確認
	if (fmt.audio_format != 1) {
		fprintf(stderr, "ERROR main: This file is not PCM format\n");
		fclose(fp);
		return -1;
	}

	if (fmt.bit_depth != 16) {
		fprintf(stderr, "ERROR main: This file is not 16bit PCM\n");
		fclose(fp);
		return -1;
	}
	fprintf(stderr, "\nmain: This file is 16bit PCM\n");

	// 最大振幅の走査
	// 1. データオフセットに移動
	if (fseek(fp, data_offset, SEEK_SET) != 0) {
		fprintf(stderr, "ERROR fread/main: Cannot move to data_offset\n");
		fprintf(stderr, "data_offset: %ld\n", data_offset);
		fclose(fp);
		return -1;
	}

	// 2. サンプルごとに読み込み、最大値を走査
		// byte_sample: blockアラインごとにサンプルを格納する変数
		// - データサンプルはblock_alignが単位なので、それ以上分割したら壊れる
	int	max_sample[2] = {0, 0};		// ゴミ値を初期化
	if (fmt.channel_num == 2) {
		// int	process_get_stereo(FILE *fp, const FmtChunk *fmt, uint32_t data_size, int *stereo_sample, int *max_sample)
		if (process_get_stereo(fp, &fmt, max_sample) == -1) {
			fprintf(stderr, "ERROR process_get_stereo/main: returned error\n");
			fclose(fp);
			return -1;
		}
	}

	printf("\nMax sound :\n");
	printf("L %d : R %d\n", max_sample[0], max_sample[1]);

	fclose(fp);
	return 0;


	// 今回はステレオ専用にして、windows_start







}
