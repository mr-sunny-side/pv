#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BUFFER_SIZE 1024
#define SEARCH_PREFIX "From: "
#define PREFIX_LEN strlen(SEARCH_PREFIX)

// 抽出と表示をストリーム処理するコード

int	ext_sender_and_copy(char *email, char *from_line)
{
	// bufferからsenderのアドレスを取得
	// emailにsender分のメモリを確保
	// emailにsenderをコピー
	char	*start = strchr(from_line, '<');
	char	*end;
	int	interval;
	if (start == NULL && (start = strchr(from_line, ' ') != NULL)) {
		start++;
		end = strchr(from_line, '\n');

	}
	else if (start != NULL) {
		start++;

	}
}

int	main(int argc, int **argv)
{
	if (argc != 2) {
		fprintf(stderr, "Argument Error\n");
		return 1;
	}

	const char	*file_name = argv[1];
	FILE		*fp = file_name;
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
			// ここでext_senderとprintf
		}
	}
}
