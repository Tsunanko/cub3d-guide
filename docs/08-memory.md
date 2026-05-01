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

## 1. このページで学ぶこと

- **リソース管理の基本**: 確保したら必ず解放
- **miniLibX リソースの解放**: image, window, display
- **エラー時の部分解放**: どこまで確保したか追跡
- **leaks / valgrind での確認**

---

## 2. 用語と仕組みの整理

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

## 3. コード解説

### cleanup.c（全解放）

```c title="cleanup.c" linenums="1"
#ifdef __linux__

// Linux 専用: ディスプレイも解放する
static void ft_destroy_mlx(void *mlx)
{
    if (mlx)
    {
        // X11 ディスプレイを切断
        mlx_destroy_display(mlx);
        // mlx 構造体自体を解放
        free(mlx);
    }
}

#else

// macOS: mlx_destroy_display がない
static void ft_destroy_mlx(void *mlx)
{
    (void)mlx;  // 未使用引数の警告を抑制
}

#endif

// config 内のメモリを解放
static void ft_free_config(t_config *config)
{
    int i;

    // 4 つのテクスチャパスを解放
    i = 0;
    while (i < 4)
    {
        if (config->tex_path[i])
            free(config->tex_path[i]);
        i++;
    }

    // マップデータ (二次元配列) を解放
    if (config->map)
    {
        i = 0;
        // 各行を解放
        while (i < config->map_h)
        {
            free(config->map[i]);
            i++;
        }
        // 行ポインタ配列を解放
        free(config->map);
    }
}

// メイン cleanup 関数
// エラー時・正常終了時の両方から呼ばれる
void ft_cleanup(t_game *game)
{
    int i;

    // 4 つのテクスチャ画像を解放
    i = 0;
    while (i < 4)
    {
        if (game->tex[i].ptr)
            mlx_destroy_image(game->mlx,
                              game->tex[i].ptr);
        i++;
    }

    // フレームバッファ (描画用 image) を解放
    if (game->frame.ptr)
        mlx_destroy_image(game->mlx,
                          game->frame.ptr);

    // ウィンドウを閉じる
    if (game->win)
        mlx_destroy_window(game->mlx, game->win);

    // ディスプレイ解放 (Linux のみ)
    ft_destroy_mlx(game->mlx);

    // config 内のメモリ解放
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

## 4. メモリ確認ツール

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

## 5. メモリ管理のチェックリスト

### 確保と解放のペア

- [ ] `malloc` の対 `free` がある
- [ ] `calloc` の対 `free` がある
- [ ] `ft_calloc` / `ft_strdup` 等も同様
- [ ] `mlx_new_image` の対 `mlx_destroy_image`
- [ ] `mlx_new_window` の対 `mlx_destroy_window`
- [ ] `mlx_xpm_file_to_image` の対 `mlx_destroy_image`
- [ ] Linux の `mlx_init` の対 `mlx_destroy_display + free`

### エラーパス

- [ ] parse エラー時にも cleanup される
- [ ] テクスチャ読み込み失敗時にも cleanup される
- [ ] ESC 終了時に cleanup される
- [ ] ウィンドウ × ボタンで cleanup される

---

## 6. 評価シートの確認項目

- [ ] `leaks` / `valgrind` でリーク 0
- [ ] 異常系（壊れたマップ等）でもリークしない
- [ ] ESC 終了時もリークしない
- [ ] `Ctrl+C` はリーク OK（シグナルハンドラ不要）

---

## 7. ディフェンスで聞かれること

| 質問 | 答え方 |
|------|--------|
| メモリリークをどう防いだ？ | 確保と解放を対にし、エラー時は errctx でグローバル登録した情報を元にクリーンアップ |
| 二次元配列の解放順は？ | 中の配列を先に解放して、最後に外の配列（行ポインタ配列）を解放 |
| NULL チェックは必要？ | `free(NULL)` は安全だが、`mlx_destroy_*` は NULL で落ちる可能性があるので必須 |
| RAII はないけどどうしてる？ | cleanup 関数を 1 つ用意し、すべてのパスから確実に呼ぶように設計 |
| valgrind で "still reachable" が出たら？ | 通常は miniLibX 内部のもの。自分のコードの `definitely lost` が 0 なら OK |

---

## 8. よくあるミス

!!! warning "エラーパスでリーク"
    正常終了は OK でも、エラー時 ( 壊れたマップなど ) で cleanup が呼ばれずリーク。

!!! warning "解放順序ミス"
    二次元配列を `free(map)` だけ先にやると中の要素が dangling に。

!!! warning "二重解放"
    同じポインタを 2 回 `free` するとクラッシュ。解放後は NULL を代入すると安全。

!!! warning "mlx の特殊リソース"
    Linux の `mlx_init` の戻り値は `free` が必要だが、macOS では不要。`#ifdef __linux__` で分岐。

---

## 9. 次のページへ

次は [09. 実際のバグと修正](09-debugging.md) で、開発中に遭遇した生のバグと直し方を学びます。
