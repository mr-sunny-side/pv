#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/*
pythonと共有するドメイン抽出関数を書く
その後、makefileみたいな感じで共有ライブラリとしてコンパイルする

※注意※ free責任は呼び出し側、つまり呼び出すpythonにあるので、free用の関数も書く
*/

//pythonから呼び出されるから、シンプルに引数の文字列からdomainを抽出し、それを返す関数
char	*ext_domain(const char *email) {
	char *here_is_at = NULL;
	char *end = NULL;

	if ((here_is_at = strchr(email, '@')) != NULL) {
		fprintf(stderr, "here_is_at is completed\n");
		here_is_at++;
	}
	else
		return NULL;


	int	interval = 0;
	char	*domain = NULL;
	if ((end = strchr(email, '>')) != NULL || (end = strchr(email, '\n')) != NULL) {
		fprintf(stderr, "strchr if is completed\n");
		interval = end - here_is_at;
		domain = malloc(interval + 1);
		if (domain == NULL)
			return NULL;

		strncpy(domain, here_is_at, interval);
		domain[interval] = '\0';
		fprintf(stderr, "domain is returned\n");
		return domain;
	}

	return NULL;

}

void	free_memory(char *str) {
	free(str);
}


int	main(int argc, char **argv) {
	if (argc != 2) {
		fprintf(stderr, "Argument Error\n");
		return 1;
	}

	const char	*test = argv[1];
	char		*result = ext_domain(test);

	printf("%s", result);
	free(result);

	return 0;
}
