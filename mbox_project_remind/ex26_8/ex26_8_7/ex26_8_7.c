#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BUFFER_SIZE 1024
#define SEARCH_PREFIX "From: "
#define PREFIX_LEN 6

int	ext_email_and_copy(char *from_line, char **email) {

	char	*start = NULL;
	char	*end = NULL;

	if ((start = strchr(from_line, '<')) != NULL) {
		start++;
		end = strchr(from_line, '>');
		if (end == NULL)
			return -1;
	} else if ((start = strchr(from_line, ' ') ) != NULL) {
		start++;
		end = strchr(from_line, '\n');
		if (end == NULL)
			return -1;
	} else
		return -1;

	int	interval = end - start;
	*email = malloc(interval + 1);
	if (*email == NULL)
		return 1;

	strncpy(*email, start, interval);
	//演算子の優先順位
	(*email)[interval] = '\0';
	return 0;
}

int	main(int argc, char **argv) {

	if (argc != 2) {
		fprintf(stderr, "Argument Error\n");
		return 1;
	}

	if (strcmp(argv[1], "-h") == 0 || strcmp(argv[1], "--help") == 0) {
		// print usage
		return 0;
	}

	const char	*file_name = argv[1];
	FILE		*fp = fopen(file_name, "r");
	if (fp == NULL) {
		fprintf(stderr, "Cannot Open File %s\n", file_name);
		return 1;
	}

	char	buffer[BUFFER_SIZE];
	char	*email = NULL;
	while (fgets(buffer, sizeof(buffer), fp) != NULL) {
		if (strncmp(buffer, SEARCH_PREFIX, PREFIX_LEN) == 0) {

			int	result = ext_email_and_copy(buffer, &email);
			if (result == -1) {
				fprintf(stderr, "Cannot Extract Email\n");
				// この場合emailは未定義なのでターンを飛ばす
				continue;
			}
			else if (result == 1) {
				fprintf(stderr, "Memory Allocation Incomplete\n");
				free(email);
				fclose(fp);
				return 1;
			}
			printf("%s\n", email);
			free(email);
			email = NULL;
		}

	}

	fclose(fp);
	return 0;

}
