import re

test_cases = [
    'From: user@example.com',
    'From: "John Doe" <john@example.com>',
    'From: notifications@github.com',
]

def extract_email(test_cases):
	for line in test_cases:
		match = re.search()
