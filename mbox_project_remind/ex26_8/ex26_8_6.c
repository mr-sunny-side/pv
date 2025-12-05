#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BUFFER_SIZE 1024
#define SEARCH_PREFIX "From: "
#define PREFIX_LEN 6

void	print_help(char *prog_name)
{
	printf("=== How to Us e===\n");
	printf("[This Program] [mbox File]\n");
	printf("\nThis program will extract sender emails from an mbox file\n");
	printf("comand '-h' of '--help' to show this message\n");
}

int	ext_sender_and_copy(char *from_line, char **email)
{

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

	char	buffer[BUFFER_SIZE];
	char	*email = NULL;
	int	line_num = 0;
	while (fgets(buffer, sizeof(buffer), fp) != NULL) {
		if (strncmp(buffer, SEARCH_PREFIX, PREFIX_LEN) == 0) {

		}
	}
}
