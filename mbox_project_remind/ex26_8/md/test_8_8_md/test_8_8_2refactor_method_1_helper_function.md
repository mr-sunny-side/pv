# リファクタリング方法1: ヘルパー関数による分割

## 概要

**既存のex26_8プロジェクトのパターンに合わせた方法**

- `ext_email_and_copy()` → 既に関数化済み
- `ext_domain()` → 既に関数化済み
- **NEW**: `process_from_line()` → From行の処理を関数化

## 設計方針

### 1. 単一責任の原則（Single Responsibility Principle）

main関数の責務：
- ファイルを開く
- 行を読む
- "From: "で始まる行を見つける
- **処理を委譲**
- ファイルを閉じる

process_from_line関数の責務：
- メールアドレスを抽出
- ドメインを抽出
- 出力
- メモリ管理

### 2. エラーハンドリングの統一

戻り値の設計：
```c
int process_from_line(char *buffer);
// 戻り値:
//   0: 成功
//  -1: メールアドレス抽出失敗
//   1: malloc失敗
```

**メリット**: mainでエラーハンドリングを一箇所に集約

## 実装例

### process_from_line() 関数

```c
/*
 * "From: "で始まる行からメールアドレス/ドメインを抽出して出力
 *
 * 引数:
 *   buffer: "From: "で始まる行
 *
 * 戻り値:
 *    0: 成功
 *   -1: メールアドレス抽出失敗
 *    1: malloc失敗（メモリ不足）
 */
int process_from_line(char *buffer) {
    char *email = NULL;
    char *domain = NULL;
    int result;

    // Step 1: メールアドレス抽出
    result = ext_email_and_copy(buffer, &email);
    if (result == -1) {
        fprintf(stderr, "Cannot extract email\n");
        return -1;
    } else if (result == 1) {
        fprintf(stderr, "ext_sender: Memory Allocation Incomplete\n");
        return 1;
    }

    // Step 2: ドメイン抽出 or メールアドレス出力
    if (strchr(email, '@') != NULL) {
        domain = ext_domain(email);
        if (domain == NULL) {
            fprintf(stderr, "ext_domain: Returned NULL\n");
            free(email);
            return 1;
        }
        printf("%s\n", domain);
        free(domain);
    } else {
        printf("%s\n", email);
    }

    free(email);
    return 0;
}
```

**ネストレベル**: 最大3（while/forなしでカウント）

### main() 関数（リファクタリング後）

```c
int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "Argument Error\n");
        return 1;
    }

    if (strcmp(argv[1], "-h") == 0 || strcmp(argv[1], "--help") == 0) {
        // print usage
        return 0;
    }

    char *file_name = argv[1];
    FILE *fp = fopen(file_name, "r");
    if (fp == NULL) {
        fprintf(stderr, "Cannot Open File %s\n", file_name);
        // 既にファイルが開けていないのでfcloseはいらない
        return 1;
    }

    char buffer[BUFFER_SIZE];
    int result;

    while (fgets(buffer, sizeof(buffer), fp) != NULL) {
        if (strncmp(buffer, SEARCH_PREFIX, PREFIX_LEN) != 0)
            continue;  // "From: "で始まらない行はスキップ

        result = process_from_line(buffer);
        if (result != 0) {
            fclose(fp);
            return result;  // -1 or 1
        }
    }

    fclose(fp);
    return 0;
}
```

**ネストレベル**: 最大2

## 改善点の詳細

### Before（現在のコード）

```c
while (fgets(...)) {                           // Level 1
    if (strncmp(...) == 0) {                   // Level 2
        result = ext_email_and_copy(...);
        if (result == -1) {                    // Level 3
            fprintf(stderr, ...);              // Level 4
            return -1;
        } else if (result == 1) {              // Level 3
            fprintf(stderr, ...);              // Level 4
            fclose(fp);
            return 1;
        } else if (strchr(email, '@') != NULL) { // Level 3
            domain = ext_domain(email);
            if (domain == NULL) {              // Level 4
                fprintf(stderr, ...);          // Level 5 ← 深すぎる！
                free(email);
                fclose(fp);
                return 1;
            }
            printf("%s\n", domain);
            free(email);
            free(domain);
        } else {
            printf("%s\n", email);
            free(email);
        }
        domain = NULL;
        email = NULL;
    }
}
```

**最深レベル**: 5
**行数**: 32行

### After（リファクタリング後）

#### main関数
```c
while (fgets(buffer, sizeof(buffer), fp) != NULL) {  // Level 1
    if (strncmp(buffer, SEARCH_PREFIX, PREFIX_LEN) != 0)  // Level 2
        continue;

    result = process_from_line(buffer);
    if (result != 0) {                               // Level 2
        fclose(fp);
        return result;
    }
}
```

**最深レベル**: 2
**行数**: 9行

#### process_from_line関数
```c
int process_from_line(char *buffer) {
    // ...
    result = ext_email_and_copy(buffer, &email);
    if (result == -1) {                    // Level 1
        fprintf(stderr, ...);
        return -1;
    } else if (result == 1) {              // Level 1
        fprintf(stderr, ...);
        return 1;
    }

    if (strchr(email, '@') != NULL) {      // Level 1
        domain = ext_domain(email);
        if (domain == NULL) {              // Level 2
            fprintf(stderr, ...);
            free(email);
            return 1;
        }
        printf("%s\n", domain);
        free(domain);
    } else {                               // Level 1
        printf("%s\n", email);
    }

    free(email);
    return 0;
}
```

**最深レベル**: 2
**行数**: 約30行

## メリット vs デメリット

### メリット

#### 1. Linuxスタイルガイドラインに準拠
- ネスト最大2レベル → **ガイドライン準拠**（最大3）
- 可読性が大幅に向上

#### 2. テストしやすい
```c
// ユニットテストの例
void test_process_from_line(void) {
    char buffer[] = "From: user@example.com\n";
    assert(process_from_line(buffer) == 0);

    char invalid[] = "From: invalid\n";
    assert(process_from_line(invalid) == -1);
}
```

#### 3. 再利用可能
- 他のプログラムでも`process_from_line()`を使える
- Pythonからも呼び出せる（ex26_8_8.cのように）

#### 4. 既存パターンに合致
- `ext_email_and_copy()`, `ext_domain()`と同様の設計
- プロジェクト全体で一貫性が保たれる

#### 5. エラーハンドリングが明確
```c
// mainでのエラーハンドリング
result = process_from_line(buffer);
if (result != 0) {
    fclose(fp);  // 確実にクローズ
    return result;
}
```

### デメリット

#### 1. 関数が増える
- 現在: 3関数（`main`, `ext_email_and_copy`, `ext_domain`）
- 変更後: 4関数（`process_from_line`が追加）

**反論**: 関数が増えても、各関数の責務が明確なら問題ない

#### 2. 関数呼び出しのオーバーヘッド
- 関数呼び出しには微小なコストがある

**反論**:
- この程度の処理では無視できるレベル
- コンパイラの最適化で`inline`展開される可能性もある
- 可読性 > パフォーマンス（マイクロ最適化は後回し）

#### 3. スタックフレームが増える
```
main
└── process_from_line
    ├── ext_email_and_copy
    └── ext_domain
```

**反論**: 深さ2のスタックは全く問題ない

## 既存コードとの比較

### ex26_8_6.c の構造

```c
int main(int argc, char **argv) {
    // ...
    while (fgets(buffer, sizeof(buffer), fp) != NULL) {
        if (strncmp(buffer, "From: ", 6) == 0) {
            if (ext_sender_and_copy(buffer, &email) == 1) {
                fprintf(stderr, "Cannot malloc email\n");
                // ...
            } else if (ext_sender_and_copy(buffer, &email) == -1) {
                // ...
            }
        }
    }
}
```

**問題点**: `ext_sender_and_copy()`を**2回呼び出している**（非効率）

### test_8_8.c（現在）の改善点

```c
result = ext_email_and_copy(buffer, &email);  // 1回だけ呼び出し
if (result == -1) {
    // ...
} else if (result == 1) {
    // ...
}
```

**改善済み**: 戻り値を変数に保存してチェック

### リファクタリング後の利点

```c
// mainはシンプルに
result = process_from_line(buffer);
if (result != 0) {
    fclose(fp);
    return result;
}
```

**さらに改善**: main関数が非常にシンプルに

## コード全体（リファクタリング後）

```c
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

*/

int ext_email_and_copy(char *from_line, char **email) {
    char *start = NULL;
    char *end = NULL;

    if ((start = strchr(from_line, '<')) != NULL) {
        start++;
        end = strchr(from_line, '>');
        if (end == NULL)
            return -1;
    } else if ((start = strchr(from_line, ' ')) != NULL) {
        start++;
        end = strchr(from_line, '\n');
        if (end == NULL)
            return -1;
    } else
        return -1;

    int interval = end - start;
    *email = malloc(interval + 1);
    if (*email == NULL)
        return 1;

    strncpy(*email, start, interval);
    //演算子の優先順位
    (*email)[interval] = '\0';
    return 0;
}

char *ext_domain(char *email) {
    char *here_is_at = NULL;

    if ((here_is_at = strchr(email, '@')) != NULL)
        here_is_at++;
    else {
        fprintf(stderr, "There is no '@'\n");
        return NULL;
    }

    int domain_len = strlen(here_is_at);
    char *result = malloc(domain_len + 1);
    if (result == NULL)
        return NULL;

    strcpy(result, here_is_at);
    return result;
}

/*
 * "From: "で始まる行からメールアドレス/ドメインを抽出して出力
 */
int process_from_line(char *buffer) {
    char *email = NULL;
    char *domain = NULL;
    int result;

    // メールアドレス抽出
    result = ext_email_and_copy(buffer, &email);
    if (result == -1) {
        fprintf(stderr, "Cannot extract email\n");
        return -1;
    } else if (result == 1) {
        fprintf(stderr, "ext_sender: Memory Allocation Incomplete\n");
        return 1;
    }

    // ドメイン抽出 or メールアドレス出力
    if (strchr(email, '@') != NULL) {
        domain = ext_domain(email);
        if (domain == NULL) {
            fprintf(stderr, "ext_domain: Returned NULL\n");
            free(email);
            return 1;
        }
        printf("%s\n", domain);
        free(domain);
    } else {
        printf("%s\n", email);
    }

    free(email);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "Argument Error\n");
        return 1;
    }

    if (strcmp(argv[1], "-h") == 0 || strcmp(argv[1], "--help") == 0) {
        // print usage
        return 0;
    }

    char *file_name = argv[1];
    FILE *fp = fopen(file_name, "r");
    if (fp == NULL) {
        fprintf(stderr, "Cannot Open File %s\n", file_name);
        // 既にファイルが開けていないのでfcloseはいらない
        return 1;
    }

    char buffer[BUFFER_SIZE];
    int result;

    while (fgets(buffer, sizeof(buffer), fp) != NULL) {
        if (strncmp(buffer, SEARCH_PREFIX, PREFIX_LEN) != 0)
            continue;

        result = process_from_line(buffer);
        if (result != 0) {
            fclose(fp);
            return result;
        }
    }

    fclose(fp);
    return 0;
}
```

## 行数比較

| 部分 | Before | After | 差分 |
|------|--------|-------|------|
| main関数 | 67行 | 42行 | -25行 |
| 新規関数（process_from_line） | - | 30行 | +30行 |
| 合計 | 130行 | 135行 | +5行 |

**結論**: 全体の行数は微増だが、各関数の責務が明確で可読性が大幅に向上

## まとめ

### この方法が適している場合

1. **既存のex26_8プロジェクトのパターンを維持したい**
2. **テストを書く予定がある**
3. **他のプログラムでも再利用したい**
4. **goto文に抵抗がある**

### 次のステップ

1. `process_from_line()`を実装
2. コンパイル: `gcc -Wall -Wextra test_8_8.c -o test_8_8`
3. テスト: `./test_8_8 mbox-short.txt`
4. Valgrindでメモリリークチェック: `valgrind --leak-check=full ./test_8_8 mbox-short.txt`

次のドキュメントでは、**goto文によるクリーンアップパターン**（Linuxカーネルスタイル）を解説する。
