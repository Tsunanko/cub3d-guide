# 01. 概要とビルド

!!! tip "ページナビ"
    **[🏠 cub3D トップ](index.md)** ・ **次 ▶️ [02. パーサー](02-parser.md)**

    **cub3D 全ページ:** [00 概要](index.md) · [**01 ビルド**](01-overview.md) · [02 パーサー](02-parser.md) · [03 レイキャスティング](03-raycasting.md) · [04 レンダリング](04-rendering.md) · [05 入力](05-input.md) · [06 メモリ](06-memory.md) · [🎓 評価対策](eval.md)

---

## このページは何？

**cub3D の全体像とビルド手順を理解するページ** です。

ソースコードがどう分かれているか、
何から読み始めればいいか、がわかります。

---

## 1. プロジェクトの全体像

### ファイル構成

```
cub3d/
├── Makefile           # ビルド設定
├── includes/
│   └── cub3d.h        # 全構造体と関数プロトタイプ
├── libs/
│   ├── libft/         # 自作標準関数ライブラリ
│   └── minilibx/      # グラフィックライブラリ
├── srcs/
│   ├── main.c         # エントリポイント
│   ├── init.c         # 初期化
│   ├── parser/        # .cub ファイル解析
│   │   ├── parse.c
│   │   ├── parse_elements.c
│   │   ├── parse_color.c
│   │   ├── parse_texture.c
│   │   ├── parse_map.c
│   │   └── parse_validate.c
│   ├── render/        # 描画
│   │   ├── render.c
│   │   ├── raycaster.c
│   │   ├── draw_column.c
│   │   └── texture.c
│   ├── input/         # キー入力
│   │   ├── input.c
│   │   └── move.c
│   └── utils/         # ユーティリティ
│       ├── cleanup.c
│       ├── error.c
│       ├── errctx.c
│       └── utils.c
├── maps/              # テスト用マップ
│   ├── valid.cub
│   └── ...
└── textures/          # 壁テクスチャ画像
```

---

## 2. 読む順番（おすすめ）

1. **`main.c`** — プログラムの入口
2. **`cub3d.h`** — 全構造体を把握
3. **`parser/parse.c`** — `.cub` ファイルの解析
4. **`render/raycaster.c`** — 光線を飛ばすアルゴリズム
5. **`render/draw_column.c`** — 壁の縦一列を描画
6. **`input/input.c`** — キー入力ハンドリング
7. **`utils/cleanup.c`** — メモリ解放

---

## 3. ビルド方法

### 必要なもの

=== "macOS"

    ```bash
    # miniLibX 用の X11 が必要
    brew install --cask xquartz
    ```

=== "Linux"

    ```bash
    # X11 開発ライブラリ
    sudo apt install libx11-dev libxext-dev libbsd-dev
    ```

### ビルドコマンド

```bash
# リポジトリに入る
cd cub3d

# ビルド
make

# 実行
./cub3D maps/valid.cub
```

### Make ルール

| コマンド | 動作 |
|------|------|
| `make` / `make all` | `cub3D` バイナリを生成 |
| `make clean` | `.o` ファイルを削除 |
| `make fclean` | `.o` とバイナリを削除 |
| `make re` | `fclean` + `all` |

---

## 4. 操作方法

| キー | 動作 |
|------|------|
| W | 前進 |
| S | 後退 |
| A | 左へ移動（ストレイフ） |
| D | 右へ移動（ストレイフ） |
| ← | 左に回転 |
| → | 右に回転 |
| ESC | 終了 |
| ウィンドウの × ボタン | 終了 |

---

## 5. 主要な構造体

`includes/cub3d.h` に定義されている主な構造体を把握しておきましょう。

### `t_vec2d` — 2D ベクトル (double)

```c
// double 型の 2D ベクトル
// プレイヤー位置、方向、光線の向き等に使う
typedef struct s_vec2d {
    double x;
    double y;
} t_vec2d;
```

### `t_vec2i` — 2D ベクトル (int)

```c
// int 型の 2D ベクトル
// ピクセル座標、マップ格子座標に使う
typedef struct s_vec2i {
    int x;
    int y;
} t_vec2i;
```

### `t_img` — miniLibX の画像

```c
// miniLibX で扱う画像の情報
typedef struct s_img {
    void *ptr;        // mlx が管理する内部ポインタ
    char *addr;       // ピクセルデータへのアドレス
    int   bpp;        // bits per pixel (通常 32)
    int   line_len;   // 1 行のバイト数
    int   endian;     // バイト順（通常 0）
    int   width;      // 画像の幅
    int   height;     // 画像の高さ
} t_img;
```

---

## 6. 実行例

```console
$ make
gcc -Wall -Wextra -Werror -c srcs/main.c -o srcs/main.o
...
$ ./cub3D maps/valid.cub
# ウィンドウが開く
# プレイヤー視点で 3D 迷路が表示される
# W/A/S/D で移動、←/→ で回転、ESC で終了
```

---

## 7. エラー時の動作

`.cub` ファイルに問題があると、プログラムは安全に終了します。

```console
$ ./cub3D maps/no_player.cub
Error
Map: no player found

$ ./cub3D maps/open_map.cub
Error
Map: not surrounded by walls

$ ./cub3D  # 引数なし
Error
Usage: ./cub3D <map.cub>
```

**評価のポイント:**
`Error\n` に続いてエラーメッセージを出す、というのが 42 の慣習です。

---

## 8. 次に読むページ

次は [パーサー](02-parser.md) で `.cub` ファイルの読み込み方法を学びましょう。
