#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define BUFFER_SIZE 1024
#define SEARCH_PREFIX "From: "
#define PREFIX_LEN 6

void	print_help(char *prog_name)
{
	printf("=== How to Use ===\n");
	printf("[%s] [mbox File]\n", prog_name);
	printf("\nThis program will extract sender emails from an mbox file\n");
	printf("command '-h' of '--help' to show this message\n");
}

int	ext_sender_and_copy(char *from_line, char **email)
{
	char	*start = NULL;
	char	*end = NULL;

	if ((start = strchr(from_line, '<')) != NULL) {
		start++;
		if ((end = strchr(from_line, '>')) == NULL)
			return 1;
	} else if ((start = strchr(from_line, ' ')) != NULL) {
		start++;
		if ((end = strchr(from_line, '\n')) == NULL)
			return 1;
	} else
		return 1;

	int	interval = end - start;
	*email = malloc(interval + 1);
	if (*email == NULL)
		return 1;
	strncpy(*email, start, interval);
	(*email)[interval] = '\0';
	return 0;
}

void	count_line(FILE *fp)
{
	// 到達していない場合、fpのポインタをそこまで進める
	// 動かすのはfget関数が返すファイル構造体のポインタなので
		// fpを動かすわけでは無い。よってasteriskは1つ

	char	c;
	// 条件式の演算子に注意
	while ((c = fgetc(fp)) != EOF && c != '\n')
		;
}

int	main(int argc, char **argv)
{
	if (argc != 2) {
		fprintf(stderr, "Argument Error\n");
		return 1;
	}

	if (strcmp(argv[1], "-h") == 0 || strcmp(argv[1], "--help") == 0) {
		print_help(argv[0]);
		return 0;
	}

	const char	*file_name = argv[1];
	FILE		*fp = fopen(file_name, "r");
	if (fp == NULL) {
		fprintf(stderr, "Cannot Open File\n");
		return 1;
	}

	time_t	start_time = clock();

	char	buffer[BUFFER_SIZE];
	char	*email = NULL;
	int	line_num = 0;
	while (fgets(buffer, sizeof(buffer), fp) != NULL) {
		size_t	len = strlen(buffer);
		// fpを動かす前に検証する必要がある
		// bufferの最後はNULL文字だから、そのまま行くと必ず動いてしまう
		if (len > 0 && buffer[len - 1] != '\n')
			count_line(fp);
		line_num++;

		if (strncmp(buffer, SEARCH_PREFIX, PREFIX_LEN) == 0) {
			if (ext_sender_and_copy(buffer, &email) == 1) {
				fprintf(stderr, "Cannot extract email\n");
				free(email);
				fclose(fp);
				return 1;
			}
			printf("%d: %s\n", line_num, email);
			free(email);
		}
	}

	time_t	end_time = clock();
	double	cpu_time = ((double)(end_time - start_time)) / CLOCKS_PER_SEC;

	// 標準出力への表示を制限している
	fprintf(stderr, "=== Statistics ===\n");
	fprintf(stderr, "\nTotal Lines: %d\n", line_num);
	fprintf(stderr, "Prosessing Time: %.3f s\n", cpu_time);


	fclose(fp);
	return 0;
}

// clock()の実装
