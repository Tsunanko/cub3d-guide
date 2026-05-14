# 07. 入力処理とプレイヤー移動

---

## このページは何？

**キーボード入力を受け取ってプレイヤーを動かす処理** を解説します。

<div class="step-flow">
  <div class="step"><span class="step-num">1</span>キー押下<br><code>W</code></div>
  <div class="step"><span class="step-num">2</span><code>keys.w = 1</code><br>にセット</div>
  <div class="step"><span class="step-num">3</span>毎フレーム<br>移動関数を<br>呼ぶ</div>
  <div class="step"><span class="step-num">4</span><code>player.pos</code><br>を更新</div>
  <div class="step"><span class="step-num">5</span>次フレームで<br>再描画</div>
</div>

**リアルタイムに動く** 仕組みはこのループで成り立っています。

---

## 🎯 なぜ入力処理を学ぶ？（学習意図）

cub3D はリアルタイムゲームなので、入力をどう扱うかで操作感が決まります。
ここで「**イベント駆動の発想**」と「**毎フレームの状態更新**」という、
GUI アプリ全般に通じる骨格を体に染み込ませます。

| 学ばせたいこと | このページで出会う形 |
|---|---|
| **イベント駆動モデル** | `mlx_hook` で押下/離すを別関数に登録 |
| **状態を保持するフラグ設計** | `t_keys` 構造体に `w/a/s/d/left/right` を bool で保持 |
| **毎フレーム判定で連続動作を作る** | `mlx_loop_hook` の中でフラグを見て移動 |
| **2D 回転行列**（線形代数の実用） | `dir` と `plane` を同じ角度で回転させる |
| **「ぶつかってもスライドする」操作感** | X と Y を別々に衝突判定する設計 |

つまり「**1 回のキー押下を 1 回の動きに変換する素朴な実装**」から脱却し、
**「押している状態」と「毎フレームの反応」を分離する** のがこのページの狙いです。

---

## このページで学ぶこと

- **`mlx_hook` のイベント番号** — `2 = KeyPress` / `3 = KeyRelease` / `17 = DestroyNotify`
- **`t_keys` 構造体** — キー状態をフラグで保持して「押しっぱなし」を実現する
- **`mlx_loop_hook` での移動更新** — 毎フレーム `ft_move` を呼ぶ理由
- **衝突判定（`ft_can_move`）** — マップ範囲外 + 壁 `'1'` をはじく
- **2D 回転行列** — `dir` と `plane` を `cos/sin` で同じ角度回す意味

---

## 1. 新しい概念の解説

### イベントループって何？

**「何か起きたら反応する」を無限に繰り返す仕組み** です。

```
while (プログラム実行中)
{
    if (キー押された) → キー処理関数を呼ぶ
    if (ウィンドウ閉じた) → 終了
    if (何もない)       → 次のフレームを描画
}
```

miniLibX ではこれを `mlx_loop()` が裏でやってくれます。
自分で書くのは **「何かあった時の処理」** だけ。

### mlx_hook って何？

**「あるイベントが起きた時に呼ぶ関数」を登録する関数** です。

```c
mlx_hook(win, イベント番号, マスク, 関数, パラメータ)
```

| イベント番号 | 意味 |
|---|---|
| 2  | キーが押された (KeyPress) |
| 3  | キーが離された (KeyRelease) |
| 17 | ウィンドウが閉じた (DestroyNotify) |

```c
// キーが押されたら ft_key_press を呼ぶ
mlx_hook(game->win, 2, 1L<<0, ft_key_press, game);
```

### コールバック関数って何？

**後から「こういう時に呼んでね」と登録する関数** です。

```
通常の関数呼び出し:
  自分 → 関数を呼ぶ

コールバック:
  自分 → 関数を登録
  miniLibX → 必要になったら登録された関数を呼ぶ
```

C では「関数のアドレス（関数ポインタ）」で登録します。

### 衝突判定って何？

**「そこに移動できるか」を確認する処理** です。

壁にめり込むのを防ぎます。

```
移動しようとする位置 (nx, ny) が…
  マップ範囲外？    → 動けない
  そこが '1' (壁)？ → 動けない
  上記以外           → 動ける
```

---

## 2. コード解説

### キー入力の処理

#### キー状態を記録する

```c title="input.c (set_key)"
// val = 1 (押された) or 0 (離された)
static void ft_set_key(int keycode, t_keys *keys, int val)
{
    if (keycode == KEY_W)
        keys->w = val;
    else if (keycode == KEY_A)
        keys->a = val;
    else if (keycode == KEY_S)
        keys->s = val;
    else if (keycode == KEY_D)
        keys->d = val;
    else if (keycode == KEY_LEFT)
        keys->left = val;
    else if (keycode == KEY_RIGHT)
        keys->right = val;
}
```

#### キー押下のハンドラ

```c title="input.c (key_press)"
int ft_key_press(int keycode, t_game *game)
{
    if (keycode == KEY_ESC)
    {
        ft_cleanup(game);
        exit(0);
    }
    ft_set_key(keycode, &game->keys, 1);
    return (0);
}
```

#### キー離した時のハンドラ

```c title="input.c (key_release)"
int ft_key_release(int keycode, t_game *game)
{
    ft_set_key(keycode, &game->keys, 0);
    return (0);
}
```

!!! info "なぜ押下と離しを分けているか？"
    **「押している間、移動し続ける」** を実現するため。

    もし `key_press` の中で直接移動させると、
    1 回押して 1 マス動くだけになります。

    フラグで状態を持ち、**毎フレーム** チェックして
    動くことで、滑らかな連続移動になります。

### 移動処理（move.c）

#### 衝突判定

```c title="move.c (can_move)"
static int ft_can_move(t_game *game, double x, double y)
{
    int mx;
    int my;

    mx = (int)x;
    my = (int)y;
    if (mx < 0 || mx >= game->config.map_w
        || my < 0 || my >= game->config.map_h)
        return (0);
    return (game->config.map[my][mx] != '1');
}
```

#### 前進・後退

```c title="move.c (forward_back)"
static void ft_move_forward_back(t_game *game)
{
    double nx;
    double ny;

    if (game->keys.w)
    {
        nx = game->player.pos.x + game->player.dir.x * MOVE_SPEED;
        ny = game->player.pos.y + game->player.dir.y * MOVE_SPEED;
        // X と Y を別々に判定 (壁沿いにスライドできるように)
        if (ft_can_move(game, nx, game->player.pos.y))
            game->player.pos.x = nx;
        if (ft_can_move(game, game->player.pos.x, ny))
            game->player.pos.y = ny;
    }
    if (game->keys.s)
    {
        nx = game->player.pos.x - game->player.dir.x * MOVE_SPEED;
        ny = game->player.pos.y - game->player.dir.y * MOVE_SPEED;
        if (ft_can_move(game, nx, game->player.pos.y))
            game->player.pos.x = nx;
        if (ft_can_move(game, game->player.pos.x, ny))
            game->player.pos.y = ny;
    }
}
```

!!! info "なぜ X と Y を別々に判定？"
    一緒に判定すると、**角にぴったりくっついて
    動けなくなる** ことがあります。

    別々に判定すると、例えば右上に動こうとして
    右に壁があっても、上だけ動ける。
    **壁沿いにスライドできる** ので操作性が良くなります。

#### 回転（三角関数）

```c title="move.c (rotate)"
static void ft_rotate(t_game *game, double angle)
{
    double old_dir_x;
    double old_plane_x;

    // dir.y の更新で dir.x を使うので保存
    old_dir_x = game->player.dir.x;
    // 2D 回転行列: x' = x*cos - y*sin, y' = x*sin + y*cos
    game->player.dir.x = game->player.dir.x * cos(angle)
        - game->player.dir.y * sin(angle);
    game->player.dir.y = old_dir_x * sin(angle)
        + game->player.dir.y * cos(angle);
    // カメラプレーンも同じ角度で回転 (視野が向きに追従)
    old_plane_x = game->player.plane.x;
    game->player.plane.x = game->player.plane.x * cos(angle)
        - game->player.plane.y * sin(angle);
    game->player.plane.y = old_plane_x * sin(angle)
        + game->player.plane.y * cos(angle);
}
```

#### メインの移動関数

```c title="move.c (move)"
void ft_move(t_game *game)
{
    ft_move_forward_back(game);
    ft_move_strafe(game);
    if (game->keys.left)
        ft_rotate(game, -ROT_SPEED);
    if (game->keys.right)
        ft_rotate(game, ROT_SPEED);
}
```

### メインループ

```c
// init.c または render.c に書かれる
int ft_loop(t_game *game)
{
    ft_move(game);
    ft_render(game);
    mlx_put_image_to_window(game->mlx, game->win, game->frame.ptr, 0, 0);
    return (0);
}

// main でフックを登録
mlx_loop_hook(game.mlx, ft_loop, &game);
mlx_hook(game.win, 2,  1L << 0, ft_key_press,   &game);
mlx_hook(game.win, 3,  1L << 1, ft_key_release, &game);
mlx_hook(game.win, 17, 0,       ft_close,       &game);
mlx_loop(game.mlx);
```

---

## 3. このページに関連する評価項目

本ページの内容は、評価シートの **以下のセクション** に対応します。詳細（英語原文 + 日本語訳 + 評価者が見るコード + Q&A）は各専用ページに。

| 評価セクション | 担当する内容 | 詳細 |
|:---|:---|:---|
| **User basic events** | × ボタン / ESC / 4 つの移動キー (W/A/S/D) / 回転キー (← / →) | [eval-events](eval-events.md) |
| **Movements** | 前進・後退・ストレイフ、左右回転、壁にめり込まないか | [eval-movement](eval-movement.md) |
| **Error management** | キーボード乱打・ボタン連打でも落ちないか | [eval-errors](eval-errors.md) |

→ 全項目を一覧したい場合は **[評価対策トップ](eval.md)** へ。

---

## 4. ディフェンスで聞かれること（学習トピック）

評価シート項目別の詳細（W/A/S/D・ESC・× ボタン・回転など）は **[eval-events](eval-events.md)** および **[eval-movement](eval-movement.md)** にあります。
ここでは **本ページの学習トピック（入力処理と移動アルゴリズム）に関する技術質問** だけを扱います。

| 質問 | 答え方 | 実装で言うと |
|---|---|---|
| イベントループとは？ | 何か起きるまで待ち、起きたらコールバック関数を呼ぶ仕組み。miniLibX の `mlx_loop` が裏で回している | `main.c` で `mlx_loop(game.mlx)` を呼ぶと制御が miniLibX に移る |
| キー押下を直接処理しない理由は？ | 押しっぱなしで連続移動を実現するため。`key_press` でフラグを立て、毎フレームチェックして動かす | `t_keys` 構造体の `w/a/s/d/left/right` フラグを `ft_set_key` で更新 |
| 衝突判定の仕組みは？ | 次の位置 (`nx`, `ny`) がマップ範囲内で、かつ `'1'` (壁) でないかチェック | `ft_can_move` がマップ外と `'1'` をはじいて 0 を返す |
| X と Y を別々に判定する理由は？ | 一緒に判定すると壁の角でスタックする。別々だと「片方の軸だけ動ける」スライド挙動になる | `ft_move_forward_back` の中で `nx` と `ny` を独立に `ft_can_move` |
| 回転はどう実装？ | 2D 回転行列 `x' = x*cos - y*sin, y' = x*sin + y*cos` を `dir` と `plane` の両方に適用 | `ft_rotate` で `old_dir_x` を保存してから両成分を更新 |
| plane を一緒に回す理由は？ | 視野角（FOV）がプレイヤーの向きに追従しないと、回ると視界がねじれる | `ft_rotate` 内で `plane` も同じ `angle` で回す |

---

## 5. よくあるミス

!!! warning "plane の回転忘れ"
    `dir` だけ回して `plane` を忘れると視野が歪む（回すほどおかしくなる）。

!!! warning "`old_dir_x` を使わない"
    `dir.x` を先に更新すると、`dir.y` の式で使う「古い値」が失われる。一時変数に保存が必須。

!!! warning "X と Y を一緒に判定"
    `ft_can_move(nx, ny)` と 1 回で判定すると、角で動けなくなる（スタック感）。

!!! warning "ESC で exit するだけ"
    `cleanup` を呼ばずに `exit` するとメモリリーク。必ず cleanup → exit の順。

---

## 💡 ここまでの学びのまとめ

このページで身についたこと:

- **イベント駆動 + フラグ + 毎フレーム判定** という 3 段構えで連続入力を扱う設計
- **押下と離す（KeyPress / KeyRelease）を別関数に登録** すれば押している間動かせる
- **X と Y を別々に衝突判定** することで角でスタックしない自然な操作感が出る
- **`dir` と `plane` を同じ角度で回す** ことで視野角が向きに追従する
- **2D 回転行列**（`cos/sin`）は線形代数の素朴な応用、`old_*` で値の参照順を保つ

!!! tip "ここで詰まったら"
    - 「Linux でキーが効かない！」→ `mlx_hook` のマスク（`1L << 0` / `1L << 1`）忘れ。詳細は [09 デバッグ事例](09-debugging.md) の バグ #1 へ
    - 「壁にめり込む！」→ `ft_can_move` の判定漏れ。マップ範囲外 + `'1'` の 2 条件をチェック
    - 「角で動けなくなる！」→ X と Y を 1 回で判定している。別々の `if` に分ける
    - 「回ると視界がねじれる！」→ `dir` だけ回して `plane` を回し忘れ。両方を同じ角度で
    - 「`dir.y` の計算がおかしい！」→ `dir.x` を先に更新してしまい元の値が失われている。`old_dir_x` に退避

---

## 6. 次のページへ

次は [メモリ管理](08-memory.md) で、リークを防ぐ方法を学びます。
