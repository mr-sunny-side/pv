#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BUFFER_SIZE 1024
#define MAX_LINE 1000
#define SEARCH_PREFIX "From: "
#define PREFIX_LEN strlen(SEARCH_PREFIX)

int	line_malloc(char **line, char *buffer, int line_num)
{
	// charは常に1byteなので、strlenで計算
	line[line_num] = malloc(strlen(buffer) + 1);
	if (line[line_num] == NULL) {
		fprintf(stderr, "Memory allocation failed\n");
		return 1;
	}
	return 0;
}

void	free_err_line(char **line, int line_num)
{
	int	i;
	for(i = 0; i < line_num; i++)
		free(line[i]);
}

void	move_fp(FILE *fp)
{
	int	c;
	while ((c = fgetc(fp)) != EOF && c != '\n') {
		;
		if (c == '\n')
			break;
	}
	printf("End of File\n");
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
	int	line_num = 1;
	int	malloc_result;
	while (line_num <= MAX_LINE && fgets(buffer, sizeof(buffer), fp) != NULL) {
		if (strncmp(buffer, SEARCH_PREFIX, PREFIX_LEN) == 0) {
			malloc_result = line_malloc(line, buffer, line_num);
			strcpy(line[line_num], buffer);
		}
		if (malloc_result == 1) {
			free_err_line(line, line_num);
			return 1;
		}


		size_t buffer_len = strlen(buffer);
		if (buffer_len > 0 && buffer[buffer_len -1] == '\n')
			line_num++;
		else {
			move_fp(fp);
			line_num++;
		}
	}
	fclose(fp);

	printf("=== Found %d matching line ===\n", line_num);
	int	i;
	for (i = 0; i < line_num; i++) {
		// 同時に開放も行う
		printf("%s\n", line[i]);
		free(line[i]);
	}
	return 0;
}
