#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BUFFER_SIZE 1024
#define SEARCH_PREFIX "From: "
#define PREFIX_LEN 6

// 抽出と表示をストリーム処理するコード

// 関数に既存のポインタに対して配列を用意してほしいなら、ポインタのポインタにする必要がある。
int	ext_sender_and_copy(char **email, char *from_line)
{
	// bufferからsenderのアドレスを取得
	// emailにsender分のメモリを確保
	// emailにsenderをコピー
	char	*start = strchr(from_line, '<');
	char	*end;
	if (start == NULL) {
		// 再代入してからインクリメントしないとNULL + 1になる
		if ((start = strchr(from_line, ' ')) != NULL)
			start++;
		else
			return 1;
		end = strchr(from_line, '\n');
		if (end == NULL)
			return 1;

	} else {
		start++;
		end = strchr(from_line, '>');
		if (end == NULL)
			return 1;
	}

	int	interval = end - start;
	*email = malloc(interval + 1);
	if (*email == NULL)
		return 1;

	strncpy(*email, start, interval);
	// ポインタのポインタを用いる際は、asteriskに注意
	// それとこのような場合は演算子の優先順位を意識する
	(*email)[interval] = '\0';
	return 0;
}

int	main(int argc, char **argv)
{
	if (argc != 2) {
		fprintf(stderr, "Argument Error\n");
		return 1;
	}

	char	*file_name = argv[1];
	FILE	*fp = fopen(file_name, "r");
	if (fp == NULL) {
		fprintf(stderr, "Cannot Open File\n");
		return 1;
	}

	char	buffer[BUFFER_SIZE];
	char	*email;
	// 今回はcharの処理なので、読み込みサイズは1024でも機能する
	// sizeof(buffer)なのは、防衛的プログラミングの一環
	while (fgets(buffer, sizeof(buffer), fp) != NULL) {
		if (strncmp(buffer, SEARCH_PREFIX, PREFIX_LEN) == 0){
			int	result = ext_sender_and_copy(&email, buffer);
			if (result == 1) {
				fprintf(stderr, "Memory allocation failed\n");
				fclose(fp);
				return 1;
			}
			printf("Line: %s", buffer);
			printf("sender: %s\n", email);
			printf("\n");
			free(email);
		}
	}

	fclose(fp);
	return 0;
}
