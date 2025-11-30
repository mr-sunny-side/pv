#include <stdio.h>
#include <stdlib.h>

int	main(int argc, char **argv)
{
	FILE	*fp;
	char	buffer[1024];
	int	line_num = 1;

	if (argc != 2)
	{
		fprintf(stderr, "Argument Error\n");
		return (1);
	}

	char	*file_name = argv[1];
	fp = fopen(file_name, "r");
	if (fp == NULL)
	{
		fprintf(stderr, "Error: Cannot Open File\n");
		return (1);
	}


	while ((line_num <= 100) && fgets(buffer, sizeof(buffer), fp) != NULL)
	{
		printf("%d: %s", line_num, buffer);
		line_num++;
	}
	fclose(fp);
	return (0);
}
