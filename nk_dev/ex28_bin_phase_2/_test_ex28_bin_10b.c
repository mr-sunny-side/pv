#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

/*
	TEST VERSION: block_align診断用

	診断内容:
	1. WAVフォーマット情報（block_align, channel_num, bit_depthなど）
	2. byte_offset が block_align の倍数かどうか
	3. fread の詳細な戻り値（feof, ferror）
	4. 読み取ったデータの16進数表示
*/

#pragma pack(push, 1)

typedef	struct {
	char		chunk_id[4];
	uint32_t	chunk_size;
	char		format[4];
} test_RiffHeader;

typedef	struct {
	char		chunk_id[4];
	uint32_t	chunk_size;
	uint16_t	audio_format;
	uint16_t	channel_num;
	uint32_t	sample_rate;
	uint32_t	byte_rate;
	uint16_t	block_align;
	uint16_t	bit_depth;
} test_FmtHeader;

typedef	struct {
	char		chunk_id[4];
	uint32_t	chunk_size;
} test_TmpHeader;

#pragma pack(pop)

int	test_get_bin(FILE *fp, test_FmtHeader *fmt, int data_size, long data_offset, float need_second) {

	uint32_t	bits_per_sample = fmt->bit_depth * fmt->channel_num;
	uint32_t	bytes_per_sample = bits_per_sample / 8;
	uint32_t	byte_rate = fmt->byte_rate;

	// === 診断1: WAVフォーマット情報を表示 ===
	fprintf(stderr, "\n=== WAV Format Info ===\n");
	fprintf(stderr, "sample_rate: %u Hz\n", fmt->sample_rate);
	fprintf(stderr, "channel_num: %u\n", fmt->channel_num);
	fprintf(stderr, "bit_depth: %u bits\n", fmt->bit_depth);
	fprintf(stderr, "byte_rate (header): %u bytes/sec\n", fmt->byte_rate);
	fprintf(stderr, "block_align (header): %u bytes\n", fmt->block_align);
	fprintf(stderr, "bits_per_sample (calc): %u bits\n", bits_per_sample);
	fprintf(stderr, "bytes_per_sample (calc): %u bytes\n", bytes_per_sample);
	fprintf(stderr, "data_size: %d bytes\n", data_size);
	fprintf(stderr, "=======================\n\n");

	if (byte_rate != bytes_per_sample * fmt->sample_rate) {
		fprintf(stderr, "test_get_bin: byte_rate formula is incorrect\n");
		return -1;
	}
	fprintf(stderr, "bytes_rate formula is correct\n");

	float	duration = (float)data_size / (float)byte_rate;
	fprintf(stderr, "duration: %.4f seconds\n", duration);

	if (duration < need_second) {
		fprintf(stderr, "test_get_bin: need_second is too big\n");
		return -1;
	}

	long	byte_offset = (long)((float)byte_rate * need_second);
	fprintf(stderr, "byte_offset(%ld) = byte_rate(%.2f) * need_second(%.2f)\n",
			byte_offset, (float)byte_rate, need_second);

	// === 診断2: block_alignの倍数かチェック ===
	long	remainder = byte_offset % fmt->block_align;
	fprintf(stderr, "byte_offset %% block_align = %ld", remainder);
	if (remainder == 0) {
		fprintf(stderr, " ✓ (aligned)\n");
	} else {
		fprintf(stderr, " ✗ (NOT aligned!)\n");
		fprintf(stderr, "WARNING: byte_offset is not aligned to block_align!\n");
		fprintf(stderr, "         This may cause reading from the middle of a frame.\n");
	}

	long	result_offset = data_offset + byte_offset;
	fprintf(stderr, "result_offset(%ld) = data_offset(%ld) + byte_offset(%ld)\n",
		result_offset, data_offset, byte_offset);

	if (fseek(fp, result_offset, SEEK_SET) != 0) {
		fprintf(stderr, "fseek/test_get_bin: returned error\n");
		return -1;
	}

	int	bin_data = 0;

	// === 診断3: freadの詳細な戻り値を確認 ===
	size_t	read_count = fread(&bin_data, bytes_per_sample, 1, fp);
	fprintf(stderr, "\n=== fread Result ===\n");
	fprintf(stderr, "fread returned: %zu (expected 1)\n", read_count);
	fprintf(stderr, "feof: %d, ferror: %d\n", feof(fp), ferror(fp));

	if (read_count != 1) {
		fprintf(stderr, "fread/test_get_bin: Cannot read bin data\n");
		return -1;
	}

	// === 診断4: 読み取ったデータを16進数で表示 ===
	fprintf(stderr, "bin_data (hex): 0x%08X\n", (unsigned int)bin_data);
	fprintf(stderr, "bin_data (dec): %d\n", bin_data);

	// 16bitステレオの場合、左右チャネルに分解
	if (bytes_per_sample == 4 && fmt->bit_depth == 16) {
		int16_t left = (int16_t)(bin_data & 0xFFFF);
		int16_t right = (int16_t)((bin_data >> 16) & 0xFFFF);
		fprintf(stderr, "Left channel:  %d (0x%04X)\n", left, (uint16_t)left);
		fprintf(stderr, "Right channel: %d (0x%04X)\n", right, (uint16_t)right);
	}
	fprintf(stderr, "===================\n\n");

	return bin_data;
}

int	test_process_read(FILE *fp, test_TmpHeader *tmp, test_FmtHeader *fmt, int *is_fmt, int *data_size, long *data_offset) {

	if (fread(tmp, sizeof(*tmp), 1, fp) != 1) {
		fprintf(stderr, "fread/test_process_read: Cannot read the file\n");
		return 1;
	}

	if (memcmp(tmp->chunk_id, "fmt ", 4) == 0) {
		fseek(fp, -sizeof(*tmp), SEEK_CUR);
		if (fread(fmt, sizeof(*fmt), 1, fp) != 1) {
			fprintf(stderr, "fread/test_process_read: Cannot read fmt chunk\n");
			return 1;
		}
		*is_fmt += 1;

		int	skip_num = (int)(fmt->chunk_size - (uint32_t)(sizeof(*fmt) - 8));
		if (fmt->chunk_size > (uint32_t)(sizeof(*fmt) - 8)) {
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
		fprintf(stderr, "Usage: %s [.wav] [seconds]\n", argv[0]);
		return -1;
	}

	const char	*file_name = argv[1];
	FILE		*fp = fopen(file_name, "rb");
	if (fp == NULL) {
		fprintf(stderr, "fopen/main: Cannot open %s\n", file_name);
		return 1;
	}

	test_RiffHeader	riff;
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

	test_FmtHeader	fmt = {0};
	test_TmpHeader	tmp = {0};
	int		is_fmt = 0;
	int		data_size = 0;
	long		data_offset = 0;
	int		result = 0;
	while (!is_fmt || !data_offset) {
		result = test_process_read(fp, &tmp, &fmt, &is_fmt, &data_size, &data_offset);
		if (result != 0) {
			fprintf(stderr, "test_process_read/main: returned error\n");
			return result;
		}
	}

	if (!is_fmt || !data_offset) {
		fprintf(stderr, "main: Cannot find fmt chunk or data offset\n");
		fclose(fp);
		return 1;
	}

	float	need_second = atof(argv[2]);
	int	bin_data = test_get_bin(fp, &fmt, data_size, data_offset, need_second);
	if (bin_data == -1) {
		fprintf(stderr, "test_get_bin/main: returned error\n");
		fclose(fp);
		return 1;
	}

	printf("\n=== Result ===\n");
	printf("bin: %0x\n", bin_data);

	fclose(fp);
	return 0;
}
