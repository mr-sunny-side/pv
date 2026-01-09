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

	if ((here_is_at = strchr(email, '@')) != NULL) {
		here_is_at++;
	}
	else
		return NULL;

	// pythonでstrip().split(b'\n')した後にどのような形になるかを考える
	int	domain_len = strlen(here_is_at);
	char	*domain = malloc(domain_len + 1);
	if (domain == NULL)
		return NULL;

	//ドメイン終端は必ず\0なので、strncpyの必要なし
	// \0の代入のも必要ない
	strcpy(domain, here_is_at);
	return domain;
}

void	free_memory(char *str) {
	free(str);
}
