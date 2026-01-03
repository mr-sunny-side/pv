#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BUFFER_SIZE 1024
#define SEARCH_PREFIX "From: "
#define PREFIX_SIZE strlen(SEARCH_PREFIX)

int	main(int argc, char **argv)
{
	if (argc != 2){
		fprintf(stderr, "Argument Error\n");
		return 1;
	}

	const char	*file_name = argv[1];
	FILE	*fp = fopen(file_name, "r");
	if (fp == NULL){
		fprintf(stderr, "Error: Cannot Open File\n");
		return 1;
	}

	// 作業用バッファ
	char	buffer[BUFFER_SIZE];
	int	line_num = 1;
	while (fgets(buffer, sizeof(buffer), fp) != NULL){
		if (!strncmp(buffer, SEARCH_PREFIX, PREFIX_SIZE))
			printf("%d: %s", line_num, buffer);

		// bufferがから出ないことを確認した上で
		// bufferの文末が\nであることを確認
		size_t	len = strlen(buffer);
		if (len > 0 && buffer[len - 1] == '\n')
			line_num++;
		// そうでなかった場合、ファイルポインタ(fp)のアドレスを\nまで移動
		// bufferに入りきらなかった残りの文を飛ばし、line_numを健全にカウントする
		else{
			// cがEOF(Eno of File?)でない且\nでもなければcontinue
			int	c;
			while ((c = fgetc(fp)) != EOF && c != '\n')
				;
			if (c == '\n')
				line_num++;
		}

	}
	fclose(fp);
	return 0;
}
