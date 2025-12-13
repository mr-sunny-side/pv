#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BUFFER_SIZE 1042
#define SEARCH_PREFIX "From: "
#define PREFIX_LEN 6

void	print_usage(char *prog_name)
{
	printf("Usage: [%s] [.mbox]\n", prog_name);
	printf("Extract senders email address from an .mbox file\n");
	printf("\nOptions:\n");
	printf(" -h --help	Show this help message\n");
}

int	ext_sender_and_copy(char *from_line, char **email)
{
	char	*start = strchr(from_line, '<');
	char	*end = NULL;
	if (start != NULL) {
		start++;
		end = strchr(from_line, '>');
		if (end == NULL)
			return 1;
	} else if ((start = strchr(from_line, ' ')) != NULL) {
		start++;
		end = strchr(from_line, '\n');
		if (end == NULL)
			return 1;
	}

	int	interval = end - start;
	*email = malloc(interval + 1);
	if (*email == NULL)
		return 1;
	strncpy(*email, start, interval);
	// 演算子の優先順位忘れがちなので特に注意
	(*email)[interval] = '\0';
	return 0;
}

int	main(int argc, char **argv)
{
	if (argc < 2) {
		fprintf(stderr, "Argument Error\n");
		return 1;
	}
	// 直接比較はできないので（アドレスの比較になる？）
	// strcmpを使う
	if (strcmp(argv[1], "-h") == 0 || strcmp(argv[1], "--help") == 0) {
		print_usage(argv[0]);
		return 0;
	}

	const char	*file_name = argv[1];
	FILE		*fp = fopen(file_name, "r");
	if (fp == NULL) {
		fprintf(stderr, "Cannot Open File\n");
		return 1;
	}

	char	buffer[BUFFER_SIZE];
	char	*email = NULL;
	while (fgets(buffer, sizeof(buffer), fp) != NULL) {
		if (strncmp(buffer, SEARCH_PREFIX, PREFIX_LEN) == 0) {
			if (ext_sender_and_copy(buffer, &email) == 0) {
				printf("email: %s\n", email);
				free(email);
			} else {
				fprintf(stderr, "Extract Failed\n");
				free(email);
				fclose(fp);
				return 1;
			}
		}
	}

	fclose(fp);
	return 0;
}

// valgrind、cppcheckを本格使用して、ロジックエラーを見つける
