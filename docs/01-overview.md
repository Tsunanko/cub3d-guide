# 01. 概要とビルド

---

## このページは何？

**cub3D の全体像とビルド手順を理解するページ** です。

ソースコードがどう分かれているか、
何から読み始めればいいか、がわかります。

---

## 🎯 なぜ「概要とビルド」を最初に学ぶ？（学習意図）

実装の細部に潜る前に、**プロジェクトの「地図」と「動かし方」を体に入れる** のがこのページの狙いです。
ファイル構成・ビルド手順・操作方法という「最初に触る部分」を押さえておくと、
以降の解説ページで「この処理はどのファイルにあって、どう起動して確かめるか」が常に明確になります。

| 学ばせたいこと | このページで出会う形 |
|---|---|
| **責務ごとのディレクトリ分け** | `parser/` `render/` `input/` `utils/` の 4 系統 |
| **Makefile の標準 4 ルール** | `all` / `clean` / `fclean` / `re` の役割 |
| **miniLibX の前提環境** | macOS の XQuartz / Linux の `libx11-dev` |
| **構造体ベースの型設計** | `t_vec2d` `t_vec2i` `t_img` を共通部品として使い回す |
| **42 流のエラー出力** | `Error\n` + メッセージ という 2 行フォーマット |

つまり「**実装に潜る前に、ビルドして起動して終了するまでを 1 周しておく**」のがこのページの狙いです。
ここを通っておけば、後続ページで「make が通らない」「実行できない」で躓くことがなくなります。

---

## このページで学ぶこと

- **ディレクトリ構成** — `srcs/parser` `srcs/render` `srcs/input` `srcs/utils` の 4 系統に分かれる理由
- **Makefile の 4 ルール** — `all` / `clean` / `fclean` / `re` がそれぞれ何を消すか
- **依存ライブラリ** — `libft` と `minilibx` の役割、X11 開発パッケージの必要性
- **共通構造体** — `t_vec2d` / `t_vec2i` / `t_img` が全コードで使い回される
- **エラー出力の形式** — 評価で必須の `Error\n` 始まりの 2 行構造

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

## 8. このページに関連する評価項目

本ページの内容は、評価シートの **以下のセクション** に対応します。詳細（英語原文 + 日本語訳 + 評価者が見るコード + Q&A）は各専用ページに。

| 評価セクション | 担当する内容 | 詳細 |
|:---|:---|:---|
| **Executable name** | 実行ファイル名 `cub3D`・`make` 後に再リンクが走らない・標準 4 ルール | [eval-execution](eval-execution.md) |
| **Error management**（部分） | `Error\n` 始まりの 2 行フォーマット・引数なし時の挙動 | [eval-errors](eval-errors.md) |

→ 全項目を一覧したい場合は **[評価対策トップ](eval.md)** へ。

---

## 9. ディフェンスで聞かれること（学習トピック）

評価シート項目別の詳細（実行ファイル名・Makefile・エラー出力など）は **[eval-execution](eval-execution.md)** にあります。
ここでは **本ページの学習トピック（プロジェクト構成とビルド）に関する技術質問** だけを扱います。

| 質問 | 答え方 | 実装で言うと |
|:---|:---|:---|
| なぜ `srcs/` をディレクトリ分けする？ | 責務ごとに分けると変更箇所が局所化されて読みやすい。パーサー / 描画 / 入力 / ユーティリティの 4 系統で分離 | `parser/` `render/` `input/` `utils/` の 4 ディレクトリ |
| `make re` は何をしている？ | `fclean` で全成果物（`.o` とバイナリ）を消し、`all` で作り直す。中間生成物が古いままバイナリだけ更新されるバグを避けられる | Makefile の `re: fclean all` |
| `libft` と `minilibx` を分けている理由は？ | 役割が違う（汎用 C 関数 vs グラフィック）し、それぞれ独自の Makefile を持つから。サブモジュール的にビルド | `libs/libft` `libs/minilibx` |
| なぜ `t_vec2d` と `t_vec2i` を別に作る？ | プレイヤー位置・光線方向は **double**、ピクセル座標やマップ格子座標は **int**。型を混ぜると暗黙変換でバグる | `t_vec2d player.pos` / `t_vec2i map_idx` |
| `Error\n` の改行はなぜ独立行？ | 42 の評価スクリプトが「最初の行が `Error` か」を見るから。1 行目に詳細を混ぜると検出に引っかかる | `ft_error` 内で `write(2, "Error\n", 6)` の後にメッセージ |

---

## 10. よくあるミス

!!! warning "実行ファイル名が小文字 `cub3d` になっている"
    subject 指定は **`cub3D`**（末尾 `D` が大文字）。Makefile の `NAME` を確認すること。
    `mv` ではなく **Makefile の `NAME` を直す** のが正解（`make re` で復活できるように）。

!!! warning "`make` 2 回目で再リンクが走る"
    依存関係（`.o` の更新規則）が間違っていると、変更がないのに毎回リンクされる。
    `make` 直後にもう 1 回 `make` を実行して **`Nothing to be done for 'all'`** が出るのが正常。

!!! warning "miniLibX のリンクライブラリ漏れ"
    macOS: `-lmlx -framework OpenGL -framework AppKit`、Linux: `-lmlx -lXext -lX11 -lm` が必要。
    片方の OS でしかビルドできない Makefile になりがち。

---

## 💡 ここまでの学びのまとめ

このページで身についたこと:

- **ディレクトリ分け** ... `parser` / `render` / `input` / `utils` の 4 系統で責務を分離する設計
- **Makefile の 4 ルール** ... `all` / `clean` / `fclean` / `re` で「作る・消す」を分ける慣習
- **依存ライブラリ** ... `libft`（自作 C 関数）と `minilibx`（X11 ベースのグラフィック）を別ビルド
- **共通構造体** ... `t_vec2d` / `t_vec2i` / `t_img` を全ファイルで使い回すことでメンバ名が統一される
- **エラー出力フォーマット** ... `Error\n` を独立行で出す 42 の慣習

!!! tip "ここで詰まったら"
    - 「`make` が通らない！」→ macOS なら `xquartz` 未導入、Linux なら `libx11-dev` 未導入の可能性
    - 「`./cub3D` がない！」→ Makefile の `NAME` が小文字 `cub3d` になっていないか確認
    - 「ウィンドウが開かない！」→ X サーバ（XQuartz / X11）が起動しているか確認

---

## 11. 次に読むページ

次は [パーサー](02-parser.md) で `.cub` ファイルの読み込み方法を学びましょう。
