# 05. カメラと魚眼補正

---

## このページは何？

**光線の「向き」をどう決めるか、そして「画面端の歪み」をどう直すかを解説するページ** です。

DDA で壁は見つけられるようになりました。
あと必要なのは:

1. 画面の各ピクセルに対応する **光線の向き**
2. 斜めの光線で起きる **魚眼歪み** の補正
3. 壁の **向き（N/S/E/W）** の判定

---

!!! info "💡 ここでつまずく人へ — 「光線」と「カメラ」の関係"
    レイキャスティングの世界では、画面 1 列ごとに 1 本の **光線 (ray)** を飛ばし、
    その光線が壁に当たった距離を計算します。
    「カメラ」は **どの方向に光線を飛ばすか** を決める役割で、
    `dir`（正面）と `plane`（横幅）の **2 本のベクトル** で表されます。

    👉 ここから先を読むときは「**光線が画面の各列を担当している**」というイメージを持つと
    一気に分かりやすくなります。

---

## 1. カメラプレーンって何？

### 🎬 プレイヤーが回転したときの視野

![プレイヤー回転](images/rotation.gif)

プレイヤー（緑の丸）が左右に回転すると、**視野の扇形** も一緒に回ります。
この扇形の **幅** を決めるのがカメラプレーン (`plane`) です。

### 定義

**視野（FOV = Field of View）を決めるベクトル** です。

プレイヤーの目には、正面の方向に **画面** があるイメージ。
その画面の幅を決めるのが **plane** ベクトルです。

```mermaid
flowchart LR
    P(プレイヤー) --> D[正面<br>dir ベクトル]
    P --> PL[視野の横幅<br>plane ベクトル]
    PL --> L[視野の左端]
    PL --> R[視野の右端]

    style P fill:#4CAF50,color:#fff,stroke:#1B5E20,stroke-width:2px
    style D fill:#FFC107,color:#000
    style PL fill:#2196F3,color:#fff
```

### 2 つのベクトルの役割

| ベクトル | 役割 |
|:---|:---|
| `player.dir` | プレイヤーが向いている方向（正面） |
| `player.plane` | その正面に垂直な「カメラの横方向」 |

**視野角（FOV）は 2 つの長さの比** で決まります。
普通は `|dir| = |plane|` で **90 度 FOV**。

---

## 2. camera_x って何？

**画面のどのピクセルかを、-1 〜 +1 の数字で表したもの** です。

### 画面座標と camera_x の対応表

| 画面の x 座標 | camera_x | 位置 |
|:-:|:-:|:---|
| 0 | **-1.0** | 左端 |
| 256 | -0.5 | 左寄り |
| 512 | **0.0** | 中央 |
| 768 | +0.5 | 右寄り |
| 1024 | **+1.0** | 右端 |

### 計算式

$$
\text{camera\_x} = \frac{2x}{\text{WIN\_W}} - 1
$$

### 光線の向きを決める

$$
\text{ray.dir} = \text{dir} + \text{plane} \times \text{camera\_x}
$$

| camera_x | 結果 | どの光線？ |
|:-:|:---|:---|
| -1 | `dir - plane` | 左端の光線 |
| 0 | `dir` | 正面の光線（まっすぐ） |
| +1 | `dir + plane` | 右端の光線 |

---

## 3. 魚眼効果（fisheye）って何？

### 🎬 魚眼補正の Before / After 比較

![魚眼補正](images/fisheye.gif)

- **左**: 補正なし → 画面端の壁が膨らんで見える（魚眼効果）
- **右**: 補正あり → 壁がまっすぐに見える（正常）

同じ視線の動きでも、補正の有無で見え方が全然違います。

### 定義

**普通の距離を使うと画面端が歪んで見える現象** です。

### なぜ歪む？

```mermaid
flowchart LR
    P(プレイヤー)
    W1[正面の壁<br>距離 5]
    W2[斜めの壁<br>距離 7]

    P ==> W1
    P ==> W2

    style P fill:#4CAF50,color:#fff
    style W1 fill:#795548,color:#fff
    style W2 fill:#795548,color:#fff
```

同じ距離にある壁でも、**斜めの光線のほうが長い**。
そのまま距離として使うと「端の壁は遠い」と勘違い → 画面端が膨らむ。

!!! info "💡 ここでつまずく人へ — `perp_wall_dist` ってなぜ必要？"
    光線の長さをそのまま使うと、画面の端の壁ほど距離が長くなり、
    **遠い = 小さく描画** されるため壁が外側に向かって縮みます（魚眼）。

    そこで「**光線の長さ**」ではなく、
    「**プレイヤーが向いている方向に投影した長さ (perpendicular distance)**」を使います。
    これで真っ直ぐな壁が画面上でも真っ直ぐ見えるようになります。

### 補正前 vs 補正後

=== "❌ 補正なし（魚眼）"

    | 画面位置 | 見え方 |
    |:-:|:---|
    | 中央 | 🧱 正常 |
    | 端 | 🎈 **膨らんで見える** |

=== "✅ 補正あり（きれい）"

    | 画面位置 | 見え方 |
    |:-:|:---|
    | 中央 | 🧱 正常 |
    | 端 | 🧱 正常（歪みなし） |

### 対策: 垂直距離を使う

光線の長さではなく、**プレイヤー正面方向への距離** だけを使います。

```mermaid
flowchart LR
    P[プレイヤー] -.斜めの光線（実際）.-> W[壁]
    P ==垂直距離（使う値）==> PR[正面方向の投影]

    style P fill:#4CAF50,color:#fff
    style PR fill:#FFC107
```

$$
\text{perp\_wall\_dist} = \text{side\_dist} - \text{delta\_dist}
$$

---

## 4. 壁の向き（N/S/E/W）をどう判定？

DDA で **最後にどちらの格子線を渡ったか** と **光線の向きの符号** で決まります。

```mermaid
flowchart LR
    S{side == 0?}
    S -->|Yes<br>X 壁| D1{dir.x > 0?}
    S -->|No<br>Y 壁| D2{dir.y > 0?}
    D1 -->|Yes 東向き| EA[EA<br>東側テクスチャ]
    D1 -->|No 西向き| WE[WE<br>西側テクスチャ]
    D2 -->|Yes 南向き| SO[SO<br>南側テクスチャ]
    D2 -->|No 北向き| NO[NO<br>北側テクスチャ]

    style EA fill:#FFE082
    style WE fill:#FFAB91
    style SO fill:#B39DDB
    style NO fill:#80CBC4
```

---

## 5. コード解説

### 光線の向き計算

```c title="raycaster.c (init_ray_dir)" linenums="1"
static void ft_init_ray_dir(t_game *game,
                            int x, t_ray *ray)
{
    double camera_x;

    // 画面の x 座標を -1〜+1 に変換
    camera_x = 2.0 * x / (double)WIN_W - 1.0;

    // 光線の向き = 正面向き + 横向き * camera_x
    ray->dir.x = game->player.dir.x
               + game->player.plane.x * camera_x;
    ray->dir.y = game->player.dir.y
               + game->player.plane.y * camera_x;

    // 今いるマスの座標を int で取得
    ray->map_pos.x = (int)game->player.pos.x;
    ray->map_pos.y = (int)game->player.pos.y;

    // 1 マス進むのに必要な光線の長さ
    if (ray->dir.x == 0)
        ray->delta_dist.x = 1e30;  // div by 0 対策
    else
        ray->delta_dist.x = fabs(1.0 / ray->dir.x);
    if (ray->dir.y == 0)
        ray->delta_dist.y = 1e30;
    else
        ray->delta_dist.y = fabs(1.0 / ray->dir.y);
}
```

### 垂直距離と壁の向き

```c title="raycaster.c (calc_wall_dist)" linenums="1"
static void ft_calc_wall_dist(t_game *game,
                               t_ray *ray)
{
    // 垂直距離 = 魚眼補正済みの正しい距離
    if (ray->side == 0)
    {
        // X 壁（東西）に当たった
        ray->perp_wall_dist =
            ray->side_dist.x - ray->delta_dist.x;
        ray->wall_x = game->player.pos.y
            + ray->perp_wall_dist * ray->dir.y;
    }
    else
    {
        // Y 壁（南北）に当たった
        ray->perp_wall_dist =
            ray->side_dist.y - ray->delta_dist.y;
        ray->wall_x = game->player.pos.x
            + ray->perp_wall_dist * ray->dir.x;
    }
    ray->wall_x -= floor(ray->wall_x);

    // どのテクスチャを使うか
    if (ray->side == 0 && ray->dir.x > 0)
        ray->tex_id = TEX_EA;  // 東
    else if (ray->side == 0 && ray->dir.x <= 0)
        ray->tex_id = TEX_WE;  // 西
    else if (ray->side == 1 && ray->dir.y > 0)
        ray->tex_id = TEX_SO;  // 南
    else
        ray->tex_id = TEX_NO;  // 北
}
```

---

## 6. 壁の高さの対応表

垂直距離から壁の高さを計算:

$$
\text{line\_h} = \frac{\text{WIN\_H}}{\text{perp\_wall\_dist}}
$$

| 距離 | 高さ（WIN_H=768） | 見え方 |
|:-:|:-:|:---|
| 1.0 | 768px | 画面いっぱい（最接近） |
| 2.0 | 384px | 半分 |
| 4.0 | 192px | 1/4 |
| 10.0 | 77px | 遠い（小さく見える） |

---

## 7. ディフェンスで聞かれること

| 質問 | 答え方 |
|------|--------|
| カメラプレーンとは？ | 視野を決める仮想の平面。`dir` と `plane` の比で FOV が決まる |
| camera_x の役割は？ | 画面のピクセル位置を -1〜+1 に変換。光線の向きを決めるのに使う |
| 魚眼補正はなぜ必要？ | 斜めの光線は長くなるので、そのまま使うと画面端が膨らむ |
| どう補正する？ | 光線の長さではなく、正面方向への投影距離（垂直距離）を使う |
| 壁の向き判定の仕組みは？ | `side` (0=X壁/1=Y壁) と光線方向の符号で決定 |

---

## 8. よくあるミス

!!! warning "魚眼補正を忘れる"
    `side_dist` をそのまま使うと画面端が膨らむ。
    必ず `perp_wall_dist = side_dist - delta_dist` を使う。

!!! warning "camera_x の符号"
    左端が `-1`、右端が `+1`。逆にすると左右が反転する。

!!! warning "壁の向き判定の反転"
    `side=0` は **東西**（EA/WE）。南北と逆にしない。

---

## 9. 次のページへ

これでレイキャスティングの 3 つの柱（DDA・カメラ・補正）が揃いました。
次は、測った距離から **実際に壁を描く方法** を学びます。

▶️ **[06. レンダリング](06-rendering.md)**
