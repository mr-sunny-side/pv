# リファクタリング方法2: gotoによるクリーンアップパターン

## 概要

**Linuxカーネルで使われている標準的なパターン**

gotoを使ってエラーハンドリングとリソース解放を一箇所に集約する。

## 重要: gotoの誤解を解く

### 一般的な誤解

> 「gotoは悪だ！スパゲッティコードになる！」

これは**Dijkstraの1968年の論文**["Go To Statement Considered Harmful"](https://homepages.cwi.nl/~storm/teaching/reader/Dijkstra68.pdf)から広まった誤解。

### Linuxカーネルの立場

[Linux Kernel Coding Style - Chapter 7: Centralized exiting of functions](https://www.kernel.org/doc/html/latest/process/coding-style.html#centralized-exiting-of-functions)より：

> Although deprecated by some people, the equivalent of the goto statement is used frequently by compilers in form of the unconditional jump instruction.
>
> **The goto statement comes in handy when a function exits from multiple locations and some common work such as cleanup has to be done.** If there is no cleanup needed then just return directly.

要約：
- **複数の出口**がある関数で、**共通のクリーンアップ処理**が必要な場合
- **gotoは推奨される**
- クリーンアップが不要なら単純に`return`すればいい

### gotoが許される条件

#### ✅ 良いgoto（Linuxスタイル）
```c
int foo(void) {
    result = do_something();
    if (result)
        goto out;

    result = do_another_thing();
    if (result)
        goto out_free_bar;

out_free_bar:
    free(bar);
out:
    return result;
}
```

**特徴**:
- **前方ジャンプのみ**（goto先は常に後ろ）
- **クリーンアップ処理に使う**
- **ラベルは関数の末尾**

#### ❌ 悪いgoto（スパゲッティコード）
```c
int bad_example(void) {
retry:  // 後方ジャンプ
    do_something();
    if (failed)
        goto retry;  // ← ループを作る（while使うべき）

    if (condition1)
        goto label1;
    else
        goto label2;

label2:
    do_thing2();
    goto end;

label1:  // ← 順序がバラバラ
    do_thing1();
    goto end;

end:
    return 0;
}
```

**問題点**:
- 後方ジャンプ（ループ作成）
- ラベルの順序がバラバラ
- 制御フローが追いにくい

## test_8_8.c へのgoto適用

### 設計方針

#### エラー時のクリーンアップ

現在の問題：
```c
// パターン1: fpのみクローズ（Line 96）
if (result == -1) {
    fprintf(stderr, "Cannot extract email\n");
    return -1;  // fcloseなし！
}

// パターン2: fpクローズ + emailなし（Line 99-100）
else if (result == 1) {
    fprintf(stderr, "ext_sender: Memory Allocation Incomplete\n");
    fclose(fp);
    return 1;
}

// パターン3: fpクローズ + emailあり（Line 106-108）
if (domain == NULL) {
    fprintf(stderr, "ext_domain: Returned NULL\n");
    free(email);
    fclose(fp);
    return 1;
}
```

**一貫性がない** → バグの温床

#### goto導入後

```c
// 全てのエラーパスで統一
if (error)
    goto cleanup;

// ...

cleanup:
    free(email);
    free(domain);
    fclose(fp);
    return result;
```

## 実装例

### main関数（リファクタリング後）

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
    char *email = NULL;
    char *domain = NULL;
    int result = 0;

    while (fgets(buffer, sizeof(buffer), fp) != NULL) {
        // "From: "で始まらない行はスキップ
        if (strncmp(buffer, SEARCH_PREFIX, PREFIX_LEN) != 0)
            continue;

        // メールアドレス抽出
        result = ext_email_and_copy(buffer, &email);
        if (result == -1) {
            fprintf(stderr, "Cannot extract email\n");
            goto cleanup_error;
        }
        if (result == 1) {
            fprintf(stderr, "ext_sender: Memory Allocation Incomplete\n");
            goto cleanup_error;
        }

        // ドメイン抽出 or メールアドレス出力
        if (strchr(email, '@') != NULL) {
            domain = ext_domain(email);
            if (domain == NULL) {
                fprintf(stderr, "ext_domain: Returned NULL\n");
                goto cleanup_error;
            }
            printf("%s\n", domain);
            free(domain);
            domain = NULL;
        } else {
            printf("%s\n", email);
        }

        free(email);
        email = NULL;
    }

    // 正常終了
    fclose(fp);
    return 0;

cleanup_error:
    free(email);
    free(domain);
    fclose(fp);
    return result;
}
```

**ネストレベル**: 最大3

## 改善点の詳細

### Before（現在のコード）

```c
while (fgets(buffer, sizeof(buffer), fp) != NULL) {
    if (strncmp(buffer, SEARCH_PREFIX, PREFIX_LEN) == 0) {
        result = ext_email_and_copy(buffer, &email);
        if (result == -1) {
            fprintf(stderr, "Cannot extract email\n");
            return -1;  // fcloseなし！
        } else if (result == 1) {
            fprintf(stderr, "ext_sender: Memory Allocation Incomplete\n");
            fclose(fp);
            return 1;
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
```

**問題点**:
1. ネストレベル5
2. エラーハンドリングが一貫していない
3. Line 96で`fclose(fp)`が漏れている

### After（goto導入後）

```c
while (fgets(buffer, sizeof(buffer), fp) != NULL) {
    if (strncmp(buffer, SEARCH_PREFIX, PREFIX_LEN) != 0)
        continue;  // ← early continueでネスト削減

    result = ext_email_and_copy(buffer, &email);
    if (result == -1) {
        fprintf(stderr, "Cannot extract email\n");
        goto cleanup_error;  // ← 統一されたクリーンアップ
    }
    if (result == 1) {
        fprintf(stderr, "ext_sender: Memory Allocation Incomplete\n");
        goto cleanup_error;
    }

    if (strchr(email, '@') != NULL) {
        domain = ext_domain(email);
        if (domain == NULL) {
            fprintf(stderr, "ext_domain: Returned NULL\n");
            goto cleanup_error;
        }
        printf("%s\n", domain);
        free(domain);
        domain = NULL;
    } else {
        printf("%s\n", email);
    }

    free(email);
    email = NULL;
}

fclose(fp);
return 0;

cleanup_error:
    free(email);   // ← 全てのエラーパスで実行
    free(domain);  // ← 全てのエラーパスで実行
    fclose(fp);    // ← 全てのエラーパスで実行
    return result;
```

**改善点**:
1. ネストレベル3
2. **全てのエラーパス**で`fclose(fp)`が実行される
3. メモリ解放も統一的に処理

## ネスト削減のテクニック

### テクニック1: Early continue

#### Before
```c
while (fgets(...)) {
    if (strncmp(...) == 0) {
        // 処理
    }
}
```

**ネスト**: Level 2

#### After
```c
while (fgets(...)) {
    if (strncmp(...) != 0)
        continue;  // ← 条件を反転して早期スキップ

    // 処理（ネストが1レベル減る）
}
```

**ネスト**: Level 1

### テクニック2: else if → 独立したif

#### Before
```c
if (result == -1) {
    // ...
} else if (result == 1) {
    // ...
}
```

**問題**: `else if`のチェーンが長くなる

#### After
```c
if (result == -1) {
    // ...
    goto cleanup_error;
}
if (result == 1) {
    // ...
    goto cleanup_error;
}
```

**改善**: 各エラーチェックが独立して明確

## Linuxカーネルの実例

### 実例1: ファイルオープン処理

Linuxカーネルの`do_sys_open()`関数から抜粋：

```c
long do_sys_open(int dfd, const char __user *filename, int flags, umode_t mode)
{
    struct open_flags op;
    int fd = build_open_flags(flags, mode, &op);
    struct filename *tmp;

    if (fd)
        return fd;

    tmp = getname(filename);
    if (IS_ERR(tmp))
        return PTR_ERR(tmp);

    fd = get_unused_fd_flags(flags);
    if (fd >= 0) {
        struct file *f = do_filp_open(dfd, tmp, &op);
        if (IS_ERR(f)) {
            put_unused_fd(fd);
            fd = PTR_ERR(f);
        } else {
            fsnotify_open(f);
            fd_install(fd, f);
        }
    }
    putname(tmp);
    return fd;
}
```

**特徴**:
- エラー時は`return`で早期終了
- リソース解放は順序通り
- gotoは使っていない（このケースでは不要）

### 実例2: メモリ確保処理

Linuxカーネルの`copy_process()`関数から抜粋（簡略化）：

```c
static struct task_struct *copy_process(...)
{
    struct task_struct *p;
    int retval = -ENOMEM;

    p = dup_task_struct(current);
    if (!p)
        goto fork_out;

    retval = copy_files(clone_flags, p);
    if (retval)
        goto bad_fork_cleanup_files;

    retval = copy_mm(clone_flags, p);
    if (retval)
        goto bad_fork_cleanup_signal;

    return p;

bad_fork_cleanup_signal:
    cleanup_signal(p);
bad_fork_cleanup_files:
    cleanup_files(p);
fork_out:
    return ERR_PTR(retval);
}
```

**特徴**:
- **複数のリソース確保**
- エラー時は**逆順でクリーンアップ**
- ラベル名が**明確**（`bad_fork_cleanup_*`）

## gotoラベルの命名規則

### Linuxスタイル

| パターン | ラベル名 | 用途 |
|---------|---------|------|
| 正常終了 | `out:` | 関数の出口 |
| エラー時クリーンアップ | `out_free:` | メモリ解放 |
| エラー時クリーンアップ（複数） | `out_free_buffer:` | 特定のリソース解放 |
| エラー時（ファイル） | `out_close:` | ファイルクローズ |
| エラー時（複合） | `cleanup_error:` | 複数のクリーンアップ |

### test_8_8.c での命名

```c
cleanup_error:  // エラー時のクリーンアップ
    free(email);
    free(domain);
    fclose(fp);
    return result;
```

**理由**:
- `cleanup_` → クリーンアップ処理であることが明確
- `error` → エラー時の処理であることが明確

## free(NULL)の安全性

### 重要な仕様

C標準（C99 7.20.3.2）より：

> The free function causes the space pointed to by ptr to be deallocated, that is, made available for further allocation. **If ptr is a null pointer, no action occurs.**

**要約**: `free(NULL)`は何もしない（安全）

### コード例

```c
char *email = NULL;
char *domain = NULL;

// エラーが起きた場合
goto cleanup_error;

cleanup_error:
    free(email);   // emailがNULLでも安全
    free(domain);  // domainがNULLでも安全
    fclose(fp);
    return result;
```

**メリット**:
- `if (email != NULL) free(email);` のチェックが不要
- クリーンアップコードがシンプルに

## メリット vs デメリット

### メリット

#### 1. エラーハンドリングの一貫性
```c
// 全てのエラーで同じパターン
if (error)
    goto cleanup_error;
```

#### 2. リソースリークの防止
```c
cleanup_error:
    free(email);   // 必ず実行
    free(domain);  // 必ず実行
    fclose(fp);    // 必ず実行
    return result;
```

#### 3. コードの重複削減
- Before: 3箇所で`fclose(fp)`を書く
- After: 1箇所だけ

#### 4. Linuxスタイルに準拠
- カーネル開発者に読みやすい
- 業界標準のパターン

#### 5. 保守性の向上
- 新しいリソースを追加する場合、クリーンアップは1箇所だけ修正

### デメリット

#### 1. gotoに対する心理的抵抗
- 「gotoは悪」という先入観
- **反論**: Linuxカーネルでは推奨されている

#### 2. ジャンプ先の追跡
- コードを読む際に`goto`先を探す必要がある
- **反論**: ラベルは常に関数末尾にあるので探しやすい

#### 3. プロジェクトで前例がない
- ex26_8シリーズで`goto`の使用例がない
- **反論**: 新しいパターンを学ぶ良い機会

## ヘルパー関数 vs goto の比較

| 観点 | ヘルパー関数 | goto |
|-----|-----------|------|
| **ネストレベル** | main: 2, helper: 2 | main: 3 |
| **関数の数** | 4個 | 3個 |
| **コードの重複** | なし | なし |
| **エラーハンドリング** | 戻り値で伝播 | ラベルで集約 |
| **テストしやすさ** | ◎（関数単位） | ○（main全体） |
| **再利用性** | ◎（他で使える） | △（mainに閉じる） |
| **Linuxスタイル準拠** | ○（間接的） | ◎（直接的） |
| **既存パターンとの整合** | ◎（合致） | △（前例なし） |
| **学習曲線** | 易しい | 中程度 |

## どちらを選ぶべきか

### ヘルパー関数が適している場合

1. **ロジックを再利用したい**（Pythonから呼ぶなど）
2. **ユニットテストを書きたい**
3. **チームメンバーがgotoに慣れていない**
4. **既存のex26_8パターンを維持したい**

### gotoが適している場合

1. **Linuxカーネルスタイルを学びたい**
2. **エラーハンドリングの一貫性を最優先**
3. **関数を増やしたくない**
4. **パフォーマンスを最大化したい**（関数呼び出しオーバーヘッド削減）

## コード全体（goto版）

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BUFFER_SIZE 1024
#define SEARCH_PREFIX "From: "
#define PREFIX_LEN 6

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
        return 1;
    }

    char buffer[BUFFER_SIZE];
    char *email = NULL;
    char *domain = NULL;
    int result = 0;

    while (fgets(buffer, sizeof(buffer), fp) != NULL) {
        if (strncmp(buffer, SEARCH_PREFIX, PREFIX_LEN) != 0)
            continue;

        result = ext_email_and_copy(buffer, &email);
        if (result == -1) {
            fprintf(stderr, "Cannot extract email\n");
            goto cleanup_error;
        }
        if (result == 1) {
            fprintf(stderr, "ext_sender: Memory Allocation Incomplete\n");
            goto cleanup_error;
        }

        if (strchr(email, '@') != NULL) {
            domain = ext_domain(email);
            if (domain == NULL) {
                fprintf(stderr, "ext_domain: Returned NULL\n");
                goto cleanup_error;
            }
            printf("%s\n", domain);
            free(domain);
            domain = NULL;
        } else {
            printf("%s\n", email);
        }

        free(email);
        email = NULL;
    }

    fclose(fp);
    return 0;

cleanup_error:
    free(email);
    free(domain);
    fclose(fp);
    return result;
}
```

## まとめ

### goto方式の特徴

1. **Linuxカーネルスタイル** → 業界標準
2. **エラーハンドリングの一貫性** → バグ防止
3. **リソースリークの防止** → 全パスで確実にクリーンアップ
4. **コードの重複削減** → DRY原則

### 推奨する学習順序

1. **まずヘルパー関数版を実装**（方法1）
   - 既存パターンに合致
   - 理解しやすい

2. **次にgoto版を実装**（方法2）
   - Linuxスタイルを学ぶ
   - エラーハンドリングの重要性を理解

3. **両方を比較**
   - どちらが読みやすいか
   - どちらが保守しやすいか
   - どちらが自分のスタイルに合うか

### 次のステップ

どちらの方法を採用しますか？
- **方法1（ヘルパー関数）**: 既存パターンとの整合性重視
- **方法2（goto）**: Linuxスタイル学習重視
- **両方試す**: 最良の選択

次のドキュメントでは、両方の方法を**実際に実装して比較**します。
