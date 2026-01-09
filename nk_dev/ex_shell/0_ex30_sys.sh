#!/bin/bash

if false; then
	=== System Directory Structure ===
	Scanned on: Wed Jan 7 15:30:00 JST 2026

	--- /bin ---
	lrwxrwxrwx 1 root root 7 Jan  1 00:00 /bin -> usr/bin
	Files: 0
	Subdirectories: 1

	--- /etc ---
	drwxr-xr-x 120 root root 12288 Jan  7 15:00 /etc
	Files: 245
	Subdirectories: 87

	...
	
	 /bin /etc /home /usr /var /tmp
fi

output="$T_FILE/0_ex30_sys.txt"

echo "=== System Directory Structure ===" >> "$output"
echo "Date: $(date)" >> $output
echo "" >> $output

for dir in /bin /etc /home /usr /var /tmp; do

	if [ -d "$dir" ]; then	
		echo "--- $dir ---" >> "$output"
		
		ls -ldh "$dir" >> $output
		
		file_count=$(find "$dir" -maxdepth 1 -type f | wc -l) 
		echo "Files: $file_count" >> $output
		
		dir_count=$(find "$dir" -maxdepth 1 -type d | wc -l)
		echo "Sub dir: $dir_count" >> $output
		
		echo "" >> $output
	else
		echo "Cannot find $dir" >> $output
	fi
done

echo "Report: $output"


