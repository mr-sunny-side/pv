#include <stdio.h>
#include <stdlib.h>

// 今後はC99を標準とする。

int	main(int argc, char **argv)
{
	FILE	*fp;
	char	buffer[1024];
	int	line_num = 1;
	char	*file_name;

	if (argc != 2)
	{
		fprintf(stderr, "Argument Error\n");
		return (1);
	}

	*file_name = argv[1];
	fp = fopen(file_name, "r");
	if (fp == NULL)
	{
		fprintf(stderr, "Error: Cannot Open File\n");
		return (1);
	}

	// 左から順に評価されるので、左に優先する条件を持ってくる
	while ((line_num <= 100) && fgets(buffer, sizeof(buffer), fp) != NULL)
	{
		printf("%d: %s", line_num, buffer);
		line_num++;
	}
	fclose(fp);
	return (0);
}
