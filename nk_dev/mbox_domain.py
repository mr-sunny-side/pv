import re

def count_domains(filepath):
    """mboxファイルのFrom:行からドメインを抽出し、出現回数を辞書で返す"""
    domain_counts = {}

    with open(filepath, encoding='utf-8') as f:
        for line in f:
            if not line.startswith('From:'):
                continue

            # メールアドレスを抽出（<user@domain> または user@domain 形式に対応）
            match = re.search(r'[\w.+-]+@([\w.-]+)', line)
            if not match:
                continue

            domain = match.group(1)
            domain_counts[domain] = domain_counts.get(domain, 0) + 1

    return domain_counts


if __name__ == '__main__':
    import sys

    filepath = sys.argv[1] if len(sys.argv) > 1 else '_mbox/google.mbox'
    counts = count_domains(filepath)

    for domain, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        print(f'{domain}: {count}')
