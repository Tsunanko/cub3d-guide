# Bonus — 評価詳細

cub3D 評価シートの **「Bonus」セクション** を「評価原文 + 日本語訳 + 実装例 + 模範回答」で 1 ボーナス項目ずつ解説します。

→ 概要は **[評価対策トップ](eval.md)** を参照。

---

## 🌱 3 秒でわかる

| 観点 | 一言で |
|---|---|
| **🎯 評価形式** | **mandatory が満点** でないと**ボーナスは完全に無視** される |
| **📦 対象項目** | 壁衝突 / ミニマップ / 開閉ドア / アニメーションスプライト / マウス回転 |
| **⚠️ ハマりどころ** | 1 点ずつ加点だが「**完全に動く** こと」が条件 / mandatory にリーク・クラッシュがあると即 0 点 |
| **🔗 評価範囲** | 0（失敗）〜 5（excellent）の 6 段階 |

---

## 📋 セクション全体の原文

!!! note "原文（評価シート Bonus）"
    > We will look at your bonuses if and only if your mandatory part is excellent. This means that you must complete the mandatory part, beginning to end, and your error management must be flawless, even in cases of twisted or bad usage. So if the mandatory part didn't score all the points during this defense bonuses will be totally ignored. When I'll be older I'll be John Carmack. Look at the subject bonus part and add one point for each bonus implemented and fully functional. Rate it from 0 (failed) through 5 (excellent).

!!! info "日本語訳"
    ボーナスを評価するのは、**マンダトリーパートが excellent（満点）の場合に限る**。これはマンダトリーを**最初から最後まで完成** させ、**エラー管理が完璧** （ねじれた使い方・悪意ある使い方を含めて）であることを意味する。よって、このディフェンスでマンダトリーが満点でなければ、**ボーナスは完全に無視** される。「将来俺は John Carmack になるんだ」。subject のボーナスパートを見て、**実装され完全に機能している** ボーナス 1 つにつき **1 点加算**。**0（失敗）〜 5（excellent）** で評価する。

!!! danger "ボーナス評価の絶対条件"

    | 条件 | 内容 |
    |:---|:---|
    | **マンダトリー満点** | 5 セクション（Preliminary / events / movement / walls / errors）が**すべて満点** |
    | **エラー管理完璧** | 「ねじれた・悪い使い方」を含めて Error management が 0 失敗 |
    | **これを満たさない場合** | ボーナス採点は**スキップ**（実装していてもゼロ評価） |

    つまり「マンダトリーが 1 つでも欠ければボーナスは見られない」。先にマンダトリーを完璧にすること。

---

## Bonus 1: Wall collisions（壁との衝突判定）

### ① 何を実装するか

> Wall collisions.

プレイヤーが壁に**めり込まない** ように、移動先のマスを判定して壁ブロックの中に入らないようにする。マンダトリーでも実装するが、ボーナスでは**より精密な衝突判定**（厚みを持った当たり判定）が期待される。

### ② 評価で見せるべき動作

| 確認 | 期待される挙動 |
|:---|:---|
| **正面で壁にぶつかる** | 完全に停止し、壁にめり込まない |
| **斜め入力で壁沿い** | X 軸または Y 軸方向だけスライド移動 |
| **コーナーでの引っかかり** | プレイヤーに**半径** を持たせ、コーナーに**0.1 マス以内** には近寄らない |
| **超高速移動でも貫通しない** | `MOVE_SPEED` を上げても、衝突判定をすり抜けない |

### ③ 実装の要点

```c title="srcs/bonus/collision_bonus.c (半径付き衝突判定)"
#define PLAYER_RADIUS 0.2
int ft_can_move(t_game *game, double nx, double ny)
{
    if (nx < 0 || ny < 0)
        return (0);
    // プレイヤーを正方形 (半径 PLAYER_RADIUS) と見なす
    int x0 = (int)(nx - PLAYER_RADIUS);
    int x1 = (int)(nx + PLAYER_RADIUS);
    int y0 = (int)(ny - PLAYER_RADIUS);
    int y1 = (int)(ny + PLAYER_RADIUS);
    if (game->config.map[y0][x0] == '1' || game->config.map[y0][x1] == '1')
        return (0);
    if (game->config.map[y1][x0] == '1' || game->config.map[y1][x1] == '1')
        return (0);
    return (1);
}
```

- マンダトリーは「点」として判定するため、コーナーで頭が壁にめり込む
- ボーナスでは**プレイヤーを円（or 正方形）** として扱い、4 隅すべてをチェック
- X と Y を**別々に判定** することで壁沿いスライドが可能に

### ④ よくある罠

- ❌ `PLAYER_RADIUS` を `0.0` のまま → コーナーで壁にめり込む（マンダトリーと同じ）
- ❌ `PLAYER_RADIUS` を大きくしすぎる → 細い通路を通れなくなる
- ❌ 4 隅判定で 1 つでも壁なら不可、にしないと**斜め越え**（壁の角を斜めに通り抜け）してしまう

---

## Bonus 2: Minimap on the screen（ミニマップ表示）

### ① 何を実装するか

> Minimap system.

画面の隅に**マップ全体の俯瞰図** を小さく描画し、プレイヤー位置と向きをリアルタイム表示する。

### ② 評価で見せるべき動作

| 確認 | 期待される挙動 |
|:---|:---|
| **画面隅に表示** | 左上または右上に重ねて描画 |
| **マップ構造** | 壁・通路がはっきり区別できる |
| **プレイヤー位置** | 移動に追従して位置マーカーが動く |
| **プレイヤー向き** | `dir` ベクトルが矢印や線で表示される |
| **半透明** | 背景の 3D ビューが透けて見える（オプション） |

### ③ 実装の要点

```c title="srcs/bonus/minimap_bonus.c (ミニマップ描画)"
#define MINI_SCALE 8     // 1 マス = 8 ピクセル
#define MINI_OFFSET_X 10
#define MINI_OFFSET_Y 10
void ft_draw_minimap(t_game *game)
{
    int y = 0;
    while (game->config.map[y]) {
        int x = 0;
        while (game->config.map[y][x]) {
            int color = (game->config.map[y][x] == '1') ? 0x444444 : 0xCCCCCC;
            ft_fill_rect(game,
                MINI_OFFSET_X + x * MINI_SCALE,
                MINI_OFFSET_Y + y * MINI_SCALE,
                MINI_SCALE, MINI_SCALE, color);
            x++;
        }
        y++;
    }
    // プレイヤー位置に赤い点
    int px = MINI_OFFSET_X + (int)(game->player.pos_x * MINI_SCALE);
    int py = MINI_OFFSET_Y + (int)(game->player.pos_y * MINI_SCALE);
    ft_fill_rect(game, px - 2, py - 2, 4, 4, 0xFF0000);
}
```

- `ft_raycast` の**直後** に `ft_draw_minimap` を呼ぶ（手前に重なる）
- マス座標 × スケール係数で画面ピクセルに変換
- プレイヤー位置・向きはレンダリングと同じ `pos_x` / `pos_y` / `dir_x` / `dir_y` を使う

### ④ よくある罠

- ❌ ミニマップを描画後にメイン画面を再描画 → ミニマップが消える
- ❌ `MINI_SCALE` が大きすぎてマップ全体がはみ出す → 画面サイズに合わせて自動スケール
- ❌ プレイヤーマーカーが大きすぎて常にマス数個分を占める → 半径 2-3 ピクセル程度に
- ❌ マップ範囲外のメモリを参照（不揃いな行長）→ `if (x < ft_strlen(map[y]))` で防御

---

## Bonus 3: Doors which can open and close（開閉ドア）

### ① 何を実装するか

> Door which can open and close.

マップに**ドア** を配置（例: `D` 文字）し、プレイヤーが**特定のキー（例 SPACE）** を押すと**目の前のドアが開閉** する。

### ② 評価で見せるべき動作

| 確認 | 期待される挙動 |
|:---|:---|
| **マップで `D` 配置** | `.cub` のマップに `D` が配置でき、パーサーが受け入れる |
| **閉じたドアは壁扱い** | 通行不可、壁テクスチャ（ドア用）が描画される |
| **開いたドアは通路扱い** | 通り抜け可、テクスチャ消失 |
| **SPACE で目の前のドア切替** | プレイヤーの目の前のドアの状態をトグル |
| **アニメーション** | （オプション）開く・閉じる際に**スライド** する |

### ③ 実装の要点

```c title="srcs/bonus/door_bonus.c (ドア状態管理)"
typedef struct s_door {
    int x;
    int y;
    int is_open;        // 0=閉 1=開
}   t_door;

void ft_toggle_door_in_front(t_game *game)
{
    // プレイヤーの前 1 マス先の座標
    int fx = (int)(game->player.pos_x + game->player.dir_x);
    int fy = (int)(game->player.pos_y + game->player.dir_y);
    t_door *d = ft_find_door(game, fx, fy);
    if (!d)
        return ;
    d->is_open ^= 1;
    if (d->is_open)
        game->config.map[fy][fx] = '0';  // 通路化
    else
        game->config.map[fy][fx] = 'D';  // 壁化
}
```

```c title="srcs/bonus/raycast_door_bonus.c (DDA でドアも壁と判定)"
// ft_dda 内
char c = game->config.map[map_y][map_x];
if (c == '1' || c == 'D')
    hit = 1;
```

- パーサーで `D` を許容する文字に追加
- ドア座標を `t_door` 配列で別途管理し、開閉状態をトグル
- レイキャストでは `'1'` と `'D'` の**両方** を壁として扱う
- ドア用テクスチャを 5 つ目として `mlx_xpm_file_to_image` で読み込み

### ④ よくある罠

- ❌ `D` を壁判定するのを忘れ → ドアが透明壁になる
- ❌ プレイヤーがドアの上で開閉してしまう → 自分の位置のドアは閉じられない判定を入れる
- ❌ 開いたドアを `'0'` に書き換えると、閉じるときに「ここは元 D だった」が分からない → `t_door` で管理
- ❌ アニメーションを入れた場合、フレーム途中で完全には開いていない状態の衝突判定が抜ける

---

## Bonus 4: Animated sprites（アニメーションスプライト）

### ① 何を実装するか

> Animated sprite.

壁ではない**フローティングオブジェクト**（敵・アイテム・松明など）を配置し、それらが**複数フレームのテクスチャを切り替えて** アニメーションする。

### ② 評価で見せるべき動作

| 確認 | 期待される挙動 |
|:---|:---|
| **スプライトが見える** | マップ内の指定位置に画像が浮かんで見える |
| **遠近感** | 近いと大きく、遠いと小さく描画される |
| **壁の手前/奥** | 壁との前後関係（depth buffer）が正しい |
| **アニメーション** | フレームごとにテクスチャが切り替わる（炎が揺らぐ、敵が歩く等） |
| **正面を向く** | スプライトは常にプレイヤー方向を向く（ビルボード） |

### ③ 実装の要点

```c title="srcs/bonus/sprite_bonus.c (スプライト描画の概要)"
typedef struct s_sprite {
    double x;
    double y;
    int frame;          // 現在のアニメーションフレーム
    t_texture *frames;  // フレーム配列
    int frame_count;
}   t_sprite;

void ft_draw_sprites(t_game *game, double *zbuffer)
{
    int i = 0;
    while (i < game->sprite_count) {
        t_sprite *sp = &game->sprites[i];
        sp->frame = (game->tick / 8) % sp->frame_count;   // 8 フレームに 1 回切替
        ft_draw_one_sprite(game, sp, zbuffer);
        i++;
    }
}
```

- 各スプライトについて、プレイヤーからの**距離** と**角度** を計算
- 画面上の x 座標と高さを計算（壁と同様の遠近感）
- **zbuffer**（各画面 x 列の壁までの距離）を使って壁の奥のスプライトは描画しない
- `tick` を増やしてフレーム番号を進める（例 60fps なら `tick/8 = 7.5fps` でアニメ）

### ④ よくある罠

- ❌ zbuffer なしで描く → 壁の前にスプライトが**いつも** 出てしまう
- ❌ 距離でソートしていない → 遠近関係が逆になる場合がある
- ❌ ビルボード（プレイヤー方向に正面を向く）処理を忘れ → スプライトが**横から見ると消える**
- ❌ アニメフレームを毎フレーム切替 → 早すぎてチラつく。8〜10 フレームに 1 回が自然

---

## Bonus 5: Mouse rotation（マウスでの視点回転）

### ① 何を実装するか

> Mouse rotation that turns the view.

マウスを**左右に動かすと視点が回転** する（FPS ゲーム標準の操作感）。

### ② 評価で見せるべき動作

| 確認 | 期待される挙動 |
|:---|:---|
| **マウス左移動** | 視点が左に回転 |
| **マウス右移動** | 視点が右に回転 |
| **滑らかさ** | 連続的にスムーズに回転（カクつかない） |
| **画面外に出ない** | マウスを動かしすぎてもポインタが画面外に行かない（中央復帰） |
| **キー回転と共存** | ← → キー回転も同時に効く |

### ③ 実装の要点

```c title="srcs/bonus/mouse_bonus.c (マウス回転)"
int ft_mouse_move(int x, int y, t_game *game)
{
    (void)y;
    int center = WIN_W / 2;
    int dx = x - game->mouse_last_x;
    if (dx != 0)
        ft_rotate(game, dx * MOUSE_SENS);
    // マウスを中央に戻す（ポインタが画面外に出ないように）
    if (x < 100 || x > WIN_W - 100) {
        mlx_mouse_move(game->mlx, game->win, center, WIN_H / 2);
        game->mouse_last_x = center;
    } else {
        game->mouse_last_x = x;
    }
    return (0);
}
```

```c title="srcs/main.c (マウスフック登録)"
mlx_hook(game.win, 6, 1L<<6, ft_mouse_move, &game);   // 6 = MotionNotify
mlx_mouse_hide(game.mlx, game.win);                    // カーソルを隠す
```

- `mlx_hook` の**イベント 6（MotionNotify）** でマウス移動を捕捉
- 前回の x と現在の x の差分（`dx`）に **感度 `MOUSE_SENS`**（例 `0.002`）を掛けて回転
- ポインタが画面外に出ないよう、端で `mlx_mouse_move` で中央に戻す
- カーソルが見えないように `mlx_mouse_hide`

### ④ よくある罠

- ❌ マウスを中央復帰しない → 画面端で動かなくなる
- ❌ 中央復帰時に `mouse_last_x` を更新しない → 一気に視点が回転して酔う
- ❌ 感度が高すぎる → 少し動かしただけで一周してしまう
- ❌ `mlx_mouse_hide` を呼ばない → カーソルが視界の真ん中で邪魔
- ❌ macOS の miniLibX にマウス関連 API がない場合がある → 環境差を確認

---

## 🎯 ディフェンス当日の動き方

!!! warning "前提: マンダトリーが満点であること"
    マンダトリー 5 セクション（Preliminary / events / movement / walls / errors）が**すべて満点** だと評価者が判断してから、初めてボーナスを見てもらえます。1 つでも欠けたら**ボーナスはスキップ**。

1. ボーナスのビルドターゲットを確認: `make bonus`（または `make` の単一ターゲット）
2. ボーナス実行ファイル名: `cub3D_bonus`（または `cub3D` に同梱）
3. **実装したボーナスを 1 つずつ実演**:
    - 壁衝突（壁にめり込まないこと、コーナー回避）
    - ミニマップ（画面隅に表示、プレイヤー追従）
    - ドア（SPACE で開閉）
    - スプライト（アニメ確認）
    - マウス回転（左右移動で回転）
4. 各ボーナスのコード抜粋を 1 ファイルずつ指す
5. **マンダトリーに影響を与えていないか**（リーク・クラッシュなし）を `leaks` で確認

!!! tip "30 秒で実演ストーリー"
    「`make bonus` でビルドします。まず壁にぶつかってめり込まないこと、コーナーをスライドできることを見せます。次に画面隅のミニマップ、プレイヤー位置と向きが移動に追従します。SPACE で目の前のドアが開閉、奥のスプライトがアニメーション、マウスで滑らかに視点回転。全部 `leaks` でリーク 0 です。」

---

## 📋 提出前最終チェック

### 前提条件

- [ ] マンダトリーが**完全に動作** している（5 セクション全部）
- [ ] マンダトリーで**メモリリーク 0**（`leaks` / `valgrind`）
- [ ] マンダトリーで**ねじれた使い方** にも `Error\n` で終了
- [ ] `Makefile` に `bonus` ターゲット（マンダトリーとファイル分離 or 同一バイナリ）

### 各ボーナス共通

- [ ] ボーナスは**完全に動作** している（半端な実装は 1 点も入らない）
- [ ] ボーナス実装によって**マンダトリー機能が壊れていない**
- [ ] ボーナスでもリーク 0
- [ ] ボーナスでも `Error\n` 経路で全リソース解放

### 個別チェック

- [ ] **Wall collisions**: コーナーでめり込まない、壁沿いスライド
- [ ] **Minimap**: 画面隅に常時表示、プレイヤー追従
- [ ] **Doors**: マップに `D` 配置可、SPACE で目の前のドア開閉、ドアが壁判定にも入っている
- [ ] **Sprites**: zbuffer で奥行き正しい、アニメフレーム切替、ビルボード
- [ ] **Mouse**: 左右移動で回転、ポインタ中央復帰、カーソル非表示

---

## 関連ページ

- 本文: [03 レイキャスティング](03-raycasting.md)
- 本文: [04 DDA アルゴリズム](04-dda.md)
- 本文: [06 レンダリング](06-rendering.md)
- 本文: [07 入力処理](07-input.md)
- 評価: [Movements の評価詳細](eval-movement.md)
- 評価: [Walls の評価詳細](eval-walls.md)
- 評価: [Error management の評価詳細](eval-errors.md)
- 評価: **[評価対策トップへ戻る](eval.md)**
