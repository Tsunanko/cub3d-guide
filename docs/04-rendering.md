# 04. レンダリング（画面に描く）

!!! tip "ページナビ"
    ◀️ 前 **[03. レイキャスティング](03-raycasting.md)** ・ **次 ▶️ [05. 入力処理](05-input.md)**

    **cub3D 全ページ:** [00 概要](index.md) · [01 ビルド](01-overview.md) · [02 パーサー](02-parser.md) · [03 レイキャスティング](03-raycasting.md) · [**04 レンダリング**](04-rendering.md) · [05 入力](05-input.md) · [06 メモリ](06-memory.md) · [🎓 評価対策](eval.md)

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

## 1. このページで学ぶこと

- **壁の高さ計算**: 距離から描画サイズを決める
- **テクスチャマッピング**: 画像を壁に貼る
- **1 ピクセルの書き込み**: miniLibX の使い方
- **床と天井**: 単色塗り

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

```c title="draw_column.c (calc_draw_params)" linenums="1"
static void ft_calc_draw_params(t_ray *ray,
                                 t_img *tex,
                                 t_draw *d)
{
    // 壁の高さ = 画面高さ / 距離
    // 距離が近いほど高く、遠いほど低い
    d->line_h = (int)(WIN_H / ray->perp_wall_dist);

    // 描画の上端 y
    // 画面中央を基準に、壁の高さ/2 だけ上
    d->draw_start = -d->line_h / 2 + WIN_H / 2;

    // 描画の下端 y
    d->draw_end = d->line_h / 2 + WIN_H / 2;

    // 画面外にはみ出したらクリッピング
    if (d->draw_start < 0)
        d->draw_start = 0;
    if (d->draw_end >= WIN_H)
        d->draw_end = WIN_H - 1;

    // テクスチャの X 座標を計算
    // wall_x は 0〜1 の小数、tex->width をかけて
    // テクスチャ上のピクセル座標にする
    d->tex_x = (int)(ray->wall_x * tex->width);

    // 壁の向きによってはテクスチャを左右反転
    // (光線の向きに合わせて表示が歪まないように)
    if (ray->side == 0 && ray->dir.x > 0)
        d->tex_x = tex->width - d->tex_x - 1;
    if (ray->side == 1 && ray->dir.y < 0)
        d->tex_x = tex->width - d->tex_x - 1;

    // テクスチャ Y 方向のステップ幅
    // 壁の高さ分描くので、テクスチャの何ピクセルずつ
    // 進むかを計算
    d->step = 1.0 * tex->height / d->line_h;

    // 最初の tex_y 位置
    // (画面クリッピングされた場合の補正を含む)
    d->tex_pos = (d->draw_start - WIN_H / 2
                  + d->line_h / 2) * d->step;
}
```

### 1 列の描画

```c title="draw_column.c (draw_column)" linenums="1"
void ft_draw_column(t_game *game, int x, t_ray *ray)
{
    t_draw  d;
    t_img   *tex;
    int     y;
    int     tex_y;
    int     color;

    // このレイが使うテクスチャを選択
    tex = &game->tex[ray->tex_id];

    // 描画パラメータを計算
    ft_calc_draw_params(ray, tex, &d);

    // ── 1. 天井部分を単色で塗る ──
    ft_draw_ceiling(game, x, d.draw_start);

    // ── 2. 壁部分をテクスチャで塗る ──
    y = d.draw_start;
    while (y <= d.draw_end)
    {
        // テクスチャの Y 座標を計算
        // (float を int に変換)
        tex_y = (int)d.tex_pos;

        // クリッピング (テクスチャ範囲外を防ぐ)
        if (tex_y >= tex->height)
            tex_y = tex->height - 1;

        // 次の行のため tex_pos を進める
        d.tex_pos += d.step;

        // テクスチャから色を取得
        color = ft_get_texel(tex, d.tex_x, tex_y);

        // 画面に 1 ピクセル書き込む
        ft_put_pixel(&game->frame, x, y, color);
        y++;
    }

    // ── 3. 床部分を単色で塗る ──
    ft_draw_floor(game, x, d.draw_end + 1);
}
```

### 天井と床（単色塗り）

```c title="draw_column.c (ceiling/floor)" linenums="1"
static void ft_draw_ceiling(t_game *game,
                             int x, int end)
{
    int y;

    y = 0;
    // y=0 から draw_start まで天井色で埋める
    while (y < end)
    {
        ft_put_pixel(&game->frame, x, y,
                     game->config.ceiling.hex);
        y++;
    }
}

static void ft_draw_floor(t_game *game,
                           int x, int start)
{
    int y;

    y = start;
    // draw_end+1 から画面下端まで床色で埋める
    while (y < WIN_H)
    {
        ft_put_pixel(&game->frame, x, y,
                     game->config.floor.hex);
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

## 5. 評価シートの確認項目

- [ ] 4 方向それぞれに対応するテクスチャが貼られる
- [ ] 近い壁は大きく、遠い壁は小さく見える
- [ ] 床と天井の色が指定通り
- [ ] 画面端でテクスチャが歪まない
- [ ] テクスチャ範囲外アクセスでクラッシュしない

---

## 6. テストチェックリスト

- [ ] 4 方向の壁テクスチャが全部違うことを目視確認
- [ ] 壁に近づくと画面が埋まる
- [ ] 離れると壁が小さくなり床/天井が広がる
- [ ] 床と天井の色が `.cub` ファイルの F/C 指定と一致
- [ ] 回転してもテクスチャが安定して表示される

---

## 7. ディフェンスで聞かれること

| 質問 | 答え方 |
|------|--------|
| テクスチャマッピングとは？ | 画像を壁に貼り付ける処理。画面のピクセルとテクスチャのピクセル（テクセル）を対応づける |
| 壁の高さはどう決める？ | `WIN_H / perp_wall_dist`。距離に反比例 |
| 壁の 4 方向をどう使い分ける？ | `ray->tex_id` に EA/WE/NO/SO のどれかをセットし、そのテクスチャを使う |
| `tex_x` を反転する理由は？ | 光線の向きによってテクスチャが左右鏡像になってしまうので補正 |
| 近づきすぎて `line_h` が巨大になったら？ | `draw_start/end` を 0〜WIN_H-1 にクリッピング |
| 床と天井はなぜ単色？ | subject 要件。テクスチャ付き床は bonus 扱い |

---

## 8. よくあるミス

!!! warning "テクスチャ範囲外アクセス"
    `tex_y >= tex->height` チェックを怠るとセグフォ。必ずクリッピング。

!!! warning "反転を忘れる"
    壁の向きによって tex_x を反転しないと、テクスチャが鏡像で貼られる。

!!! warning "frame に書き込まず window に書く"
    mlx_pixel_put は遅い。`ft_put_pixel` で自前の image buffer に書いて、一度に `mlx_put_image_to_window` するのが高速。

!!! warning "天井と床の色を RGB→HEX 変換忘れ"
    `F 220,100,0` の 3 整数を `0xDC6400` に変換する処理が必要。

---

## 9. 次のページへ

次は [入力処理](05-input.md) で、キー入力とプレイヤー移動を学びます。
