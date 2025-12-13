#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BUFFER_SIZE 1024
#define MAX_LINE 1000
#define SEARCH_PREFIX "From: "
#define PREFIX_LEN strlen(SEARCH_PREFIX)

int	line_malloc(char **line, char *buffer, int idx)
{
	// charは常に1byteなので、strlenで計算
	line[idx] = malloc(strlen(buffer) + 1);
	if (line[idx] == NULL) {
		fprintf(stderr, "Memory allocation failed\n");
		return 1;
	}
	return 0;
}

void	free_err_line(char **line, int idx)
{
	int	i;
	for(i = 0; i < idx; i++)
		free(line[i]);
}

void	move_fp(FILE *fp)
{
	// この関数はポインタを動かすだけなので、確実に'\n'で止まる記述は不要
	int	c;
	while ((c = fgetc(fp)) != EOF && c != '\n')
		;

}

int	main(int argc, char **argv)
{
	if (argc != 2) {
		fprintf(stderr, "Argument Error\n");
		return 1;
	}

	const char	*file_name = argv[1];
	FILE	*fp = fopen(file_name, "r");
	if (fp == NULL) {
		fprintf(stderr, "Cannot Open File\n");
		return 1;
	}

	char	buffer[BUFFER_SIZE];
	char	*line[MAX_LINE];
	// indexで何を数えているのか、indexとして使うのにふさわしいかは非常に重要な観点である
	int	idx = 0;
	// 確実に代入されない変数は初期化する事
	int	malloc_result = 0;
	while (idx <= MAX_LINE && fgets(buffer, sizeof(buffer), fp) != NULL) {
		if (strncmp(buffer, SEARCH_PREFIX, PREFIX_LEN) == 0) {
			malloc_result = line_malloc(line, buffer, idx);
			strcpy(line[idx], buffer);
			idx++;
		}
		if (malloc_result == 1) {
			free_err_line(line, idx);
			return 1;
		}
	}
	fclose(fp);

	printf("=== Found %d matching line ===\n", idx);
	int	i;
	for (i = 0; i < idx; i++) {
		// 同時に開放も行う
		printf("%s", line[i]);
		free(line[i]);
	}
	return 0;
}
