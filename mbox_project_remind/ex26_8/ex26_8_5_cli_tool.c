#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BUFFER_SIZE 1042
#define SEARCH_PREFIX "From: "
#define PREFIX_LEN 6

int	main(int argc, char **argv)
{
	if (argc < 2) {
		fprintf(stderr, "Argument Error\n");
		return 1;
	}
	if (argv[1] == "-h" || argv[1] == "--help") {
		// helpの表示
		return 0;
	}

	const char	*file_name = argv[1];
	FILE		*fp = fopen(file_name, "r");
	if (fp == NULL) {
		fprintf(stderr, "Cannot Open File\n");
		return 1;
	}

	char	buffer[BUFFER_SIZE];
	char	*email;
	while (fgets(buffer, sizeof(buffer), fp) != NULL) {
		if (strncmp(buffer, SEARCH_PREFIX, PREFIX_LEN) == 0) {
			// ext_sender_and_copy
			// printf
			// free(email)
		}
	}
}
