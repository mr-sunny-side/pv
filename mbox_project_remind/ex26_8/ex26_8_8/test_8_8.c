#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BUFFER_SIZE 1024
#define SEARCH_PREFIX "From: "
#define PREFIX_LEN 6

/*
	このファイルでext_senderとext_domainの実装を行う
	その上で、python実装時に起きるエラーを特定

	※ex26_8_8.cのロジックエラーがしっくりこなかったので、復習も兼ねる

*/

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

char	*ext_domain(const char	*email) {

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

}
