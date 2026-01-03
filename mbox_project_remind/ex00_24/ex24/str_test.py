import sys

matched_count = 10
recipient = sys.argv[1]
label = 'matched ' + recipient + ' count:'
print(f"Label length: {len(label)}")
print(f"Label: '{label}'")
print(f"Formatted: '{label:<30}'")
print(f"Full line: |{label:<30}|{matched_count:>15}|")
