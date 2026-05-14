# 08. メモリ管理

---

## このページは何？

**cub3D で確保したメモリを、確実にすべて解放する方法** を解説します。

42 の評価では **メモリリークがあると即 0 点**。
cub3D は特に解放対象が多いので、**計画的な管理** が必要です。

```
解放が必要なもの:
  □ マップデータ (二次元配列)
  □ テクスチャパス 4 つ
  □ miniLibX 画像 5 つ (テクスチャ 4 + フレーム 1)
  □ miniLibX ウィンドウ
  □ miniLibX ディスプレイ (Linux のみ)
```

---

## 🎯 なぜメモリ管理を学ぶ？（学習意図）

cub3D は **長時間動き続けるプログラム** で、確保するリソースの種類が一気に増えます。
ここで「**確保したものを最後まで責任を持って解放する**」という C プログラマの基本動作を、
**多種類リソース + エラーパスあり** という難条件で身につけます。

| 学ばせたいこと | このページで出会う形 |
|---|---|
| **確保と解放のペアリング** | `malloc` ↔ `free`、`mlx_new_*` ↔ `mlx_destroy_*` の対 |
| **C には GC も RAII もない**現実 | 全パス（正常 + 異常）から自力で cleanup を呼ぶ設計 |
| **二次元配列の解放順** | 内側 → 外側の順、逆だと dangling pointer |
| **NULL セーフな解放**（`if (ptr)`） | `mlx_destroy_*` は NULL で落ちる可能性があるので保護 |
| **環境差異**（Linux と macOS のリソース差） | `#ifdef __linux__` で `mlx_destroy_display` を分岐 |

つまり「**マルチリソースのライフサイクルを、エラー経路も含めて全部管理する**」のがこのページの狙いです。

---

## このページで学ぶこと

- **`ft_cleanup`** — 4 つのテクスチャ + フレーム + ウィンドウ + mlx を順に解放する集約関数
- **`ft_free_config`** — マップの二次元配列とテクスチャパス文字列を解放
- **`errctx`（エラーコンテキスト）** — エラー時にどこまで確保したかを追跡する仕組み
- **`#ifdef __linux__`** — `mlx_destroy_display` + `free` が必要なのは Linux のみ
- **`valgrind` / `leaks`** — リークが本当に 0 か外部ツールで検証する手順

---

## 1. 用語と仕組みの整理

### メモリリーク（memory leak）

**`malloc` で確保したメモリを `free` し忘れて残り続けること** です。

```c
char *s = malloc(100);
// 使う
// ...
// free(s) を忘れて関数終了 → リーク
```

短時間で終わるプログラムなら OS がまとめて回収するので表面化しにくいですが、
ゲームのように **長時間動き続けるプログラム** では、使い終わったメモリが
蓄積していきパフォーマンス低下や異常終了を招きます。

!!! danger "42 の評価ではリーク = 即 0 点"
    評価ツール（`valgrind` / `leaks`）で 1 バイトでもリークが検出されると、
    その exercise は不合格になります。cub3D でも当然ゼロを目指します。

### なぜ C では特に気をつける必要があるか

C 言語には **自動でメモリを片付けてくれる仕組みが無い** からです。

| 言語 | 解放のしくみ |
|:---|:---|
| Python / Java / Go 等 | GC（ガベージコレクタ）が自動で解放 |
| C++ | スコープを抜けると **デストラクタが自動で解放**（RAII） |
| **C** | **全部自分で `free` を呼ぶ必要がある** |

特に厄介なのが **エラー途中の経路**。確保した直後にエラーが起きると、
その都度全部のリソースを解放しないとリークします。

```
正常パス:   確保 → 使う → 解放 ✓
エラーパス: 確保 → エラー → そのまま exit → リーク ✗
```

### cub3D で解放すべきもの

cub3D ではこれまでの課題と違って **解放対象の種類が多い** ので整理が必要です。

| 解放対象 | 個数 | 解放関数 |
|:---|:-:|:---|
| マップの二次元配列 | 高さ + 1 | `free` |
| テクスチャパス文字列 | 4 つ | `free` |
| miniLibX 画像 | 5 つ（テクスチャ4+フレーム1） | `mlx_destroy_image` |
| miniLibX ウィンドウ | 1 つ | `mlx_destroy_window` |
| miniLibX ディスプレイ | 1 つ（Linux のみ） | `mlx_destroy_display` + `free` |

**解放の順序や NULL チェックを間違える** と、二重解放やクラッシュを起こします。

### エラーコンテキスト（errctx）

cub3D で採用している **「エラー発生時にどこまで確保したか」を追跡する仕組み** です。

```c
// 確保する前に登録しておく
ft_set_errctx(config, lines);

// どこかでエラー発生
ft_error("...");
// ↓ ft_error 内部で errctx を見て
//   それまでに確保したものを全部解放してから exit
```

グローバル変数で持つのは C の古典的なパターン。
`ft_error` がどこから呼ばれても **確実に cleanup できる** ようにする工夫です。

---

## 2. コード解説

### cleanup.c（全解放）

```c title="cleanup.c"
#ifdef __linux__
// Linux 専用: ディスプレイも解放する
static void ft_destroy_mlx(void *mlx)
{
    if (mlx)
    {
        mlx_destroy_display(mlx);
        free(mlx);
    }
}
#else
// macOS: mlx_destroy_display がない
static void ft_destroy_mlx(void *mlx)
{
    (void)mlx;
}
#endif

static void ft_free_config(t_config *config)
{
    int i;

    i = 0;
    while (i < 4)
    {
        if (config->tex_path[i])
            free(config->tex_path[i]);
        i++;
    }
    if (config->map)
    {
        i = 0;
        while (i < config->map_h)
        {
            free(config->map[i]);
            i++;
        }
        free(config->map);
    }
}

// エラー時・正常終了時の両方から呼ばれる
void ft_cleanup(t_game *game)
{
    int i;

    i = 0;
    while (i < 4)
    {
        if (game->tex[i].ptr)
            mlx_destroy_image(game->mlx, game->tex[i].ptr);
        i++;
    }
    if (game->frame.ptr)
        mlx_destroy_image(game->mlx, game->frame.ptr);
    if (game->win)
        mlx_destroy_window(game->mlx, game->win);
    ft_destroy_mlx(game->mlx);
    ft_free_config(&game->config);
}
```

!!! info "`if (ptr)` のチェックが重要"
    エラーで途中終了した場合、**確保前のポインタは NULL**（`ft_bzero` でゼロクリア済み）。

    NULL を `free` するのは C では安全ですが、
    `mlx_destroy_*` は NULL でクラッシュする可能性があるので、
    必ず NULL チェックしてから呼びます。

### 二次元配列の解放パターン

```c
// 確保
char **map = calloc(rows + 1, sizeof(char *));
for (int i = 0; i < rows; i++)
    map[i] = malloc(cols);
// 解放 (逆順)
for (int i = 0; i < rows; i++)
    free(map[i]);  // 各行を先に解放
free(map);         // 行ポインタ配列を最後に
```

**解放順序を間違えると未定義動作** になるので注意。

---

## 3. メモリ確認ツール

### Linux: valgrind

```bash
valgrind --leak-check=full \
         --show-leak-kinds=all \
         ./cub3D maps/valid.cub
```

出力例:

```
==12345== HEAP SUMMARY:
==12345==     in use at exit: 0 bytes in 0 blocks
==12345==   total heap usage: 142 allocs, 142 frees, ...
==12345==
==12345== All heap blocks were freed -- no leaks are possible
```

**`definitely lost`** が **0 bytes** なら OK。

### macOS: leaks

```bash
leaks --atExit -- ./cub3D maps/valid.cub
```

miniLibX は macOS ではリークを出すことがあるので、
**自分のコードからのリークだけ** を確認します。

---

## 4. このページに関連する評価項目

本ページの内容は、評価シートの **以下のセクション** に対応します。詳細（英語原文 + 日本語訳 + 評価者が見るコード + Q&A）は専用ページに。

| 評価セクション | 担当する内容 | 詳細 |
|:---|:---|:---|
| **Error management** | 異常マップ / ESC / × / 乱打のいずれの経路でもリーク 0、`leaks` / `valgrind` で検証 | [eval-errors](eval-errors.md) |

→ 全項目を一覧したい場合は **[評価対策トップ](eval.md)** へ。

---

## 5. ディフェンスで聞かれること（学習トピック）

評価シート項目別の詳細（リーク 0 の根拠・確認手順）は **[eval-errors](eval-errors.md)** にあります。
ここでは **本ページの学習トピック（メモリ管理の設計）に関する技術質問** だけを扱います。

| 質問 | 答え方 | 実装で言うと |
|---|---|---|
| メモリリークをどう防いだ？ | 確保と解放を対にし、エラー時は `errctx` でグローバル登録した情報を元にクリーンアップ | `ft_set_errctx` 登録 → `ft_error` 内部で `ft_cleanup` を呼んで `exit` |
| 二次元配列の解放順は？ | 中の配列を先に解放してから、最後に外の配列（行ポインタ配列）を解放 | `ft_free_config` のループで `free(map[i])` → `free(map)` |
| NULL チェックは必要？ | `free(NULL)` は安全だが、`mlx_destroy_*` は NULL で落ちる可能性があるので必須 | `ft_cleanup` で `if (game->tex[i].ptr)` / `if (game->win)` を毎回確認 |
| RAII はないけどどうしてる？ | `ft_cleanup` 関数を 1 つ用意し、すべてのパス（正常終了・ESC・× ・エラー）から確実に呼ぶように設計 | `ft_close_window` / `ft_key_press`（ESC）/ `ft_error` 全てが `ft_cleanup` 経由 |
| valgrind で "still reachable" が出たら？ | 通常は miniLibX 内部のもの。自分のコードの `definitely lost` が 0 なら OK | `definitely lost: 0 bytes in 0 blocks` を必ず確認 |
| なぜ `mlx_destroy_display` が macOS にないの？ | macOS の miniLibX は Cocoa（NSApp）を内部で持つ別実装で、ディスプレイの概念が違うため | `#ifdef __linux__` でラップして Linux のみ呼ぶ |

---

## 6. よくあるミス

!!! warning "エラーパスでリーク"
    正常終了は OK でも、エラー時 ( 壊れたマップなど ) で cleanup が呼ばれずリーク。

!!! warning "解放順序ミス"
    二次元配列を `free(map)` だけ先にやると中の要素が dangling に。

!!! warning "二重解放"
    同じポインタを 2 回 `free` するとクラッシュ。解放後は NULL を代入すると安全。

!!! warning "mlx の特殊リソース"
    Linux の `mlx_init` の戻り値は `free` が必要だが、macOS では不要。`#ifdef __linux__` で分岐。

---

## 💡 ここまでの学びのまとめ

このページで身についたこと:

- **確保と解放のペアリング** が C プログラムの基本動作（`malloc` ↔ `free`、`mlx_new_*` ↔ `mlx_destroy_*`）
- **`ft_cleanup` という集約関数** を全パスから呼ぶことで、C でも RAII 相当の安全性を確保できる
- **`errctx` でエラー時の解放対象を追跡** する古典的パターン（グローバル変数の正当な使い方）
- **NULL セーフな解放**：`free(NULL)` は安全だが `mlx_destroy_*` は危険なので必ず `if (ptr)`
- **`#ifdef __linux__` で環境差を吸収**：Linux のみ `mlx_destroy_display` + `free` が必要

!!! tip "ここで詰まったら"
    - 「`valgrind` で `definitely lost` が出る！」→ 確保したのに `ft_cleanup` 内で解放していないリソースがある。新しく `mlx_new_*` を追加したら `ft_cleanup` も同時に更新
    - 「`mlx_destroy_*` でクラッシュする！」→ NULL チェックを忘れている。`if (ptr)` を全箇所で
    - 「Linux だけリークする！」→ `mlx_init` の戻り値 + `mlx_destroy_display` の解放忘れ。`#ifdef __linux__` の分岐を確認
    - 「エラー時だけリーク！」→ `ft_error` の中で `ft_cleanup` が呼ばれていない or `errctx` に未登録。エラーパスを追って確認

---

## 7. 次のページへ

次は [09. 実際のバグと修正](09-debugging.md) で、開発中に遭遇した生のバグと直し方を学びます。
