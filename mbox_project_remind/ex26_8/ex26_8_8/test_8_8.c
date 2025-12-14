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

	1. ネストが深すぎてエラーを見つけるのが困難なので、linuxスタイルの書き方を学ぶ
	2. 関数ロジック自体に問題はなさそうなので、python側の最適化をする
		- 原因はext_senderを仲介することで、email文字列の末尾が想定と違ったこと
		- なので、ext_domainだけで動作するように書き直す or 動作を修正

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

char	*ext_domain(char *email) {

	char	*here_is_at = NULL;

	if ((here_is_at = strchr(email, '@')) != NULL)
		here_is_at++;
	else {
		return NULL;
	}

	int	domain_len = strlen(here_is_at);
	char	*result = malloc(domain_len + 1);
	if (result == NULL)
		return NULL;

	strcpy(result, here_is_at);
	return result;
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

	char	*file_name = argv[1];
	FILE		*fp = fopen(file_name, "r");
	if (fp == NULL) {
		fprintf(stderr, "Cannot Open File %s\n", file_name);
		// 既にファイルが開けていないのでfcloseはいらない
		return 1;
	}


	char		buffer[BUFFER_SIZE];
	char		*email = NULL;
	char		*domain = NULL;
	int		result = 0;
	while (fgets(buffer, sizeof(buffer), fp) != NULL) {
		if (strncmp(buffer, SEARCH_PREFIX, PREFIX_LEN) == 0) {
			result = ext_email_and_copy(buffer, &email);
			if (result == -1) {
				fprintf(stderr, "Cannot extract email\n");
				return -1;
			} else if (result == 1) {
				fprintf(stderr, "ext_sender: Memory Allocation Incomplete\n");
				fclose(fp);
				return 1;
			// @があるかチェックしたうえでext_domainに渡す
			} else if (strchr(email, '@') != NULL) {
				domain = ext_domain(email);
				if (domain == NULL) {
					fprintf(stderr, "ext_domain: Returned NULL\n");
					free(email);
					fclose(fp);
					return 1;
				}
				printf("%s\n", domain);
				free(email);
				free(domain);
			// ext_senderが真で@がないなら、そのままemailを出力
			} else {
				printf("%s\n", email);
				free(email);
			}
			domain = NULL;
			email = NULL;

		}
	}

	fclose(fp);
	return 0;
}

// まずconstのせいで死ぬほどややこしいので使わないことにした
// 作成した結果、@の有無でエラーは起きなかった
