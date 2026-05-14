# 06. レンダリング — 画面に描く

---

## このページは何？

**光線の測定結果から、実際に画面に絵を描く処理** を解説します。

前ページ（レイキャスティング）で「壁までの距離」と
「どのテクスチャを使うか」が決まりました。
このページではそれを使って **1 本の縦線** を描画します。

```
1 ピクセル幅の縦線を描画 × 画面横幅の回数

+-- 1 ピクセル幅の縦線 --+
|   天井色              |  ← 上部: 天井
+-----------------------+
|                       |
|  テクスチャの          |  ← 中央: 壁
|  縦 1 列             |
|                       |
+-----------------------+
|    床色               |  ← 下部: 床
+-----------------------+
```

---

## 🎯 なぜレンダリングを学ぶ？（学習意図）

DDA で距離が、カメラで光線方向と壁面の向きが揃いました。最後のピースは
**「測定結果 → ピクセル」** の変換です。ここでは「距離と高さの反比例」「テクスチャ座標の縦横変換」
「フレームバッファに直接書き込む高速化テクニック」という、3D ゲームの **描画パイプラインの最終段** を学びます。

| 学ばせたいこと | このページで出会う形 |
|---|---|
| **遠近法と距離の反比例** | `line_h = WIN_H / perp_wall_dist` で「遠いほど小さく」を 1 行で実現 |
| **テクスチャマッピング** | テクセル (texel) と画面ピクセルの 1 対 1 対応を `tex_x` / `tex_y` で計算 |
| **U 座標 (`wall_x`) と V 座標 (`tex_pos`)** | 横は壁の当たり位置、縦は描画 y の比例配分という別軸の発想 |
| **フレームバッファ直書き** | `mlx_pixel_put` ではなく `frame.addr` に直接書く高速化 → smooth な表示 |
| **クリッピング** | `draw_start / draw_end` を 0〜WIN_H にクランプして近すぎる壁で破綻しない |
| **テクスチャ反転** | 光線方向によって `tex_x = width - tex_x - 1` で鏡像反転する 4 通り |

つまり「**測定された 1 つの距離値が、64×64 のテクスチャの 1 列を縦伸縮しながら画面に転写される**」
というパイプラインを **手で書く** ことで、3D 描画の本質を掴むのがこのページの狙いです。
ここを抜けると cub3D は完成形にぐっと近づきます。

---

## 1. このページで学ぶこと

- **`line_h`** — 距離から壁の高さを決める計算（反比例）
- **`draw_start` / `draw_end`** — 描画範囲のクリッピング
- **`tex_x` (U 座標)** — `wall_x` × `tex->width` でテクスチャの横位置
- **`tex_pos` / `step` (V 座標)** — 画面 y の進みに対してテクスチャ y がどう進むか
- **`ft_put_pixel`** — フレームバッファに 1 px 書き込むイディオム（`endian` / `line_len` / `bpp`）
- **テクスチャ左右反転** — `side` × `dir` で 4 方向のうち 2 方向は `tex_x` を反転
- **天井と床の単色塗り** — `mandatory` の要件と `bonus` の境界

---

## 2. 新しい概念の解説

### テクスチャマッピングって何？

**壁に画像を貼り付ける処理** です。

壁テクスチャは 64x64 や 128x128 の画像ファイル。
距離に応じて **画像を縦に伸縮** して描画します。

```
テクスチャ (64x64)       画面の縦線 (距離による)
+-----+                  +-+   ← 遠い壁は小さく
| 画像 |                  | |
|     |       →          | |
|     |                  +-+
+-----+

                         +---+
                         |   |
                         |   |  ← 近い壁は大きく
                         |   |
                         |   |
                         +---+
```

### pixel put って何？

**1 個の点を画面に描く関数** です。

miniLibX では直接ピクセルにアクセスして書き込みます。

```c
// ft_put_pixel(画像, x, y, 色)
// → 画像の (x, y) ピクセルを指定色にする
```

色は **ARGB** 形式の 32bit int。

```
0xFF0000   = 赤
0x00FF00   = 緑
0x0000FF   = 青
0xFFFFFF   = 白
0x000000   = 黒
```

### texel（テクセル）って何？

**テクスチャ上の 1 ピクセル** のことです。

画面上のピクセルを描画するために、
対応するテクスチャのピクセル（テクセル）を取り出します。

---

## 3. コード解説

### プログラムの流れ

```
ft_draw_column(game, x, ray)
  ↓
calc_draw_params: 描画範囲とテクスチャ座標を計算
  ↓
draw_ceiling: 上部を天井色で塗る
  ↓
ループ: テクスチャから色を取り出して縦ラインを描く
  ↓
draw_floor: 下部を床色で塗る
```

### 描画パラメータの計算

```c title="draw_column.c (calc_draw_params)"
static void ft_calc_draw_params(t_ray *ray, t_img *tex, t_draw *d)
{
    // 壁の高さ = 画面高さ / 距離 (距離が近いほど高く)
    d->line_h = (int)(WIN_H / ray->perp_wall_dist);
    d->draw_start = -d->line_h / 2 + WIN_H / 2;
    d->draw_end = d->line_h / 2 + WIN_H / 2;
    if (d->draw_start < 0)
        d->draw_start = 0;
    if (d->draw_end >= WIN_H)
        d->draw_end = WIN_H - 1;
    // wall_x (0〜1) を tex->width 倍してテクスチャ X 座標に
    d->tex_x = (int)(ray->wall_x * tex->width);
    // 光線の向きに合わせてテクスチャを左右反転
    if (ray->side == 0 && ray->dir.x > 0)
        d->tex_x = tex->width - d->tex_x - 1;
    if (ray->side == 1 && ray->dir.y < 0)
        d->tex_x = tex->width - d->tex_x - 1;
    // テクスチャ Y 方向のステップ幅
    d->step = 1.0 * tex->height / d->line_h;
    d->tex_pos = (d->draw_start - WIN_H / 2 + d->line_h / 2) * d->step;
}
```

### 1 列の描画

```c title="draw_column.c (draw_column)"
void ft_draw_column(t_game *game, int x, t_ray *ray)
{
    t_draw  d;
    t_img   *tex;
    int     y;
    int     tex_y;
    int     color;

    tex = &game->tex[ray->tex_id];
    ft_calc_draw_params(ray, tex, &d);
    ft_draw_ceiling(game, x, d.draw_start);
    y = d.draw_start;
    while (y <= d.draw_end)
    {
        tex_y = (int)d.tex_pos;
        if (tex_y >= tex->height)
            tex_y = tex->height - 1;
        d.tex_pos += d.step;
        color = ft_get_texel(tex, d.tex_x, tex_y);
        ft_put_pixel(&game->frame, x, y, color);
        y++;
    }
    ft_draw_floor(game, x, d.draw_end + 1);
}
```

### 天井と床（単色塗り）

```c title="draw_column.c (ceiling/floor)"
static void ft_draw_ceiling(t_game *game, int x, int end)
{
    int y;

    y = 0;
    while (y < end)
    {
        ft_put_pixel(&game->frame, x, y, game->config.ceiling.hex);
        y++;
    }
}

static void ft_draw_floor(t_game *game, int x, int start)
{
    int y;

    y = start;
    while (y < WIN_H)
    {
        ft_put_pixel(&game->frame, x, y, game->config.floor.hex);
        y++;
    }
}
```

---

## 4. テクスチャ座標の直感的理解

```
プレイヤーから見た壁:

+-------- 壁 --------+
| texture (64x64)   |
|                   |
| wall_x = 0.3      |  ← 壁の 30% の位置に当たった
| → tex_x = 19      |    (64 * 0.3 = 19)
|                   |
+-------------------+

tex_x が決まったら、
縦 1 列分を tex_pos を進めながら読み取る:

tex[0][19]  ← 天井寄り
tex[1][19]
tex[2][19]
...
tex[63][19] ← 床寄り
```

---

## 5. このページに関連する評価項目

本ページの内容は、評価シートの **以下のセクション** に対応します。詳細（英語原文 + 日本語訳 + 評価者が見るコード + Q&A）は各専用ページに。

| 評価セクション | 担当する内容 | 詳細 |
|:---|:---|:---|
| **Walls** | 4 方向（NO/SO/EA/WE）テクスチャの貼り分け、壁の歪みのなさ、距離に応じた高さ | [eval-walls](eval-walls.md) |
| **Technical elements of the display** | フレームバッファ直書きによる smooth な描画、天井/床の色塗り、ウィンドウ表示の整合性 | [eval-display](eval-display.md) |

→ 全項目を一覧したい場合は **[評価対策トップ](eval.md)** へ。

---

## 6. ディフェンスで聞かれること（学習トピック）

評価シート項目別の詳細（4 方向テクスチャ・smooth な描画など）は **[eval-walls](eval-walls.md)** / **[eval-display](eval-display.md)** にあります。
ここでは **本ページの学習トピック（描画パイプライン）に関する技術質問** だけを扱います。

| 質問 | 答え方 | 実装で言うと |
|:---|:---|:---|
| テクスチャマッピングとは？ | 画像を壁に貼り付ける処理。画面のピクセル ↔ テクスチャのピクセル（テクセル）を対応づける | `ft_get_texel(tex, tex_x, tex_y)` で 1 テクセル取り出し、`ft_put_pixel` で画面に転写 |
| 壁の高さはどう決める？ | `WIN_H / perp_wall_dist`。距離に **反比例** = 近いほど高く、遠いほど低い | `ft_calc_draw_params` の `d->line_h = (int)(WIN_H / ray->perp_wall_dist);` |
| `tex_x` (U 座標) はどう求める？ | DDA から得た `wall_x` (0〜1) を `tex->width` 倍。壁の当たり位置の小数部 × テクスチャ幅 | `d->tex_x = (int)(ray->wall_x * tex->width);` |
| `tex_pos` / `step` (V 座標) の仕組みは？ | 画面 y を 1 進めるごとにテクスチャ y を `step = tex->height / line_h` だけ進める。距離が近くて `line_h` が大きいときは細かく進む | 描画ループ内で `d.tex_pos += d.step;` を毎行加算 |
| 壁の 4 方向をどう使い分ける？ | `ray->tex_id` に NO/SO/EA/WE のどれかをセット（前ページのカメラ処理で決定）、そのテクスチャ画像を使う | `tex = &game->tex[ray->tex_id];` で 4 つの中から選択 |
| `tex_x` を反転する理由は？ | 光線の向きによってテクスチャが左右鏡像になってしまう。`side` × `dir` の符号を見て 4 方向のうち 2 方向は反転する | `if (ray->side == 0 && ray->dir.x > 0) d->tex_x = tex->width - d->tex_x - 1;` |
| 近づきすぎて `line_h` が巨大になったら？ | `draw_start / draw_end` を 0〜WIN_H-1 にクリッピング。壁に密着しても落ちない | `if (d->draw_start < 0) d->draw_start = 0;` |
| なぜ `mlx_pixel_put` を直接使わない？ | 1 px ごとに X サーバへの round-trip が発生して遅い。`ft_put_pixel` で自前バッファに書き、最後に 1 回だけ `mlx_put_image_to_window` するのが定石 | `ft_put_pixel` は `frame.addr` ポインタ計算で書き込み、`render.c` 末尾で 1 回転送 |
| 床と天井はなぜ単色？ | subject 要件。テクスチャ付き床は **bonus** 扱い | `ft_draw_ceiling` / `ft_draw_floor` でループ単色塗り |

---

## 7. よくあるミス

!!! warning "テクスチャ範囲外アクセス"
    `tex_y >= tex->height` チェックを怠るとセグフォ。必ずクリッピング。

!!! warning "反転を忘れる"
    壁の向きによって tex_x を反転しないと、テクスチャが鏡像で貼られる。

!!! warning "frame に書き込まず window に書く"
    mlx_pixel_put は遅い。`ft_put_pixel` で自前の image buffer に書いて、一度に `mlx_put_image_to_window` するのが高速。

!!! warning "天井と床の色を RGB→HEX 変換忘れ"
    `F 220,100,0` の 3 整数を `0xDC6400` に変換する処理が必要。

---

## 💡 ここまでの学びのまとめ

このページで身についたこと:

- **`line_h = WIN_H / perp_wall_dist`** で距離 → 高さの反比例を 1 行で表現
- **U 座標 (`tex_x`) と V 座標 (`tex_pos`)** の 2 軸でテクスチャの 1 列を画面に貼る
- **`step = tex->height / line_h`** という増分計算で、近い壁も遠い壁も同じループで描ける
- **フレームバッファ直書き** が smooth な描画の鍵 — `mlx_pixel_put` は使わない
- **`side` × `dir` の符号で `tex_x` を反転** することで 4 方向のテクスチャが正しい向きで貼られる
- **クリッピング (`draw_start/end` クランプ)** で近接時の負値・はみ出しを防ぐ

!!! tip "ここで詰まったら"
    - 「テクスチャが鏡像になる！」→ `tex_x = tex->width - tex_x - 1` の反転条件（`side` × `dir`）を見直す
    - 「壁に近づくと SEGV！」→ `draw_start < 0` / `draw_end >= WIN_H` のクリッピング忘れ。`line_h` が巨大化している
    - 「描画が遅い/カクつく！」→ `mlx_pixel_put` を使っていないか確認。`ft_put_pixel` で `frame.addr` 直書きに変更
    - 「テクスチャに変な色が混じる！」→ `tex_y >= tex->height` のクランプ忘れ、または `endian` / `line_len` / `bpp` の扱いミス
    - 「床と天井の色が違う！」→ `.cub` の `F`/`C` の 3 整数 → HEX 変換（`(r << 16) | (g << 8) | b`）が抜けている
    - 「4 方向どれも同じテクスチャ！」→ 前ページ `ft_calc_wall_dist` で `tex_id` の分岐が機能していない

---

## 8. 次のページへ

次は [入力処理](07-input.md) で、キー入力とプレイヤー移動を学びます。
