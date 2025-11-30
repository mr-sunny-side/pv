#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int	main(int argc, char **argv)
{
	if (argc != 2){
		fprintf(stderr, "Argument Error\n");
		return (1);
	}

	char	*file_name = argv[1];
	FILE	*fp = fopen(file_name, "r");
	if (fp == NULL){
		fprintf(stderr, "Error: Cannot Open File\n");
		return (1);
	}

	// 作業用バッファ
	char	buffer[1024];
	char	s2[] = "From: ";
	int	line_num = 1;
	while (line_num <= 1000 && fgets(buffer, sizeof(buffer), fp) != NULL){
		if (!strncmp(buffer, s2, strlen(s2)))
			printf("%d: %s", line_num, buffer);
		line_num++;
	}
	fclose(fp);
	return (0);
}
