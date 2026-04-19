# 05. 入力処理とプレイヤー移動

!!! tip "ページナビ"
    ◀️ 前 **[04. レンダリング](04-rendering.md)** ・ **次 ▶️ [06. メモリ管理](06-memory.md)**

    **cub3D 全ページ:** [00 概要](index.md) · [01 ビルド](01-overview.md) · [02 パーサー](02-parser.md) · [03 レイキャスティング](03-raycasting.md) · [04 レンダリング](04-rendering.md) · [**05 入力**](05-input.md) · [06 メモリ](06-memory.md) · [🎓 評価対策](eval.md)

---

## このページは何？

**キーボード入力を受け取ってプレイヤーを動かす処理** を解説します。

```
キー押下 (W)
   ↓
keys.w = 1 にセット
   ↓
毎フレーム移動関数を呼ぶ
   ↓
player.pos を更新
   ↓
次フレームで再描画
```

**リアルタイムに動く** 仕組みはこのループで成り立っています。

---

## 1. このページで学ぶこと

- **イベントループ**: miniLibX の `mlx_loop`
- **キーフック**: `mlx_hook` によるキー登録
- **キー押下 / 離す**: 状態を `keys` 構造体に保存
- **移動と衝突判定**: 次の位置が通れるか確認
- **回転**: 三角関数で向きを変える

---

## 2. 新しい概念の解説

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

## 3. コード解説

### キー入力の処理

#### キー状態を記録する

```c title="input.c (set_key)" linenums="1"
// キーに対応するフラグをセット/クリア
// val = 1 (押された) or 0 (離された)
static void ft_set_key(int keycode,
                        t_keys *keys, int val)
{
    // W キー
    if (keycode == KEY_W)
        keys->w = val;
    // A キー (左ストレイフ)
    else if (keycode == KEY_A)
        keys->a = val;
    // S キー (後退)
    else if (keycode == KEY_S)
        keys->s = val;
    // D キー (右ストレイフ)
    else if (keycode == KEY_D)
        keys->d = val;
    // ← キー (左回転)
    else if (keycode == KEY_LEFT)
        keys->left = val;
    // → キー (右回転)
    else if (keycode == KEY_RIGHT)
        keys->right = val;
}
```

#### キー押下のハンドラ

```c title="input.c (key_press)" linenums="1"
// キーが押されたときに呼ばれる
int ft_key_press(int keycode, t_game *game)
{
    // ESC は即終了
    if (keycode == KEY_ESC)
    {
        ft_cleanup(game);  // メモリ解放
        exit(0);
    }
    // 他のキーはフラグを 1 にセット
    ft_set_key(keycode, &game->keys, 1);
    return (0);
}
```

#### キー離した時のハンドラ

```c title="input.c (key_release)" linenums="1"
// キーが離されたときに呼ばれる
int ft_key_release(int keycode, t_game *game)
{
    // フラグを 0 にクリア
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

```c title="move.c (can_move)" linenums="1"
// 指定位置に移動可能か判定
static int ft_can_move(t_game *game,
                        double x, double y)
{
    int mx;
    int my;

    // float → int で格子座標に変換
    mx = (int)x;
    my = (int)y;

    // マップ範囲外は移動不可
    if (mx < 0 || mx >= game->config.map_w
        || my < 0 || my >= game->config.map_h)
        return (0);

    // そこが壁('1') でなければ移動可
    return (game->config.map[my][mx] != '1');
}
```

#### 前進・後退

```c title="move.c (forward_back)" linenums="1"
static void ft_move_forward_back(t_game *game)
{
    double nx;  // 次の X 位置
    double ny;  // 次の Y 位置

    // W: 前進
    if (game->keys.w)
    {
        // プレイヤーの向き方向に MOVE_SPEED 進む
        nx = game->player.pos.x
           + game->player.dir.x * MOVE_SPEED;
        ny = game->player.pos.y
           + game->player.dir.y * MOVE_SPEED;

        // X と Y を別々に判定
        // (角でぴったり止まらず壁沿いに動くため)
        if (ft_can_move(game, nx,
                        game->player.pos.y))
            game->player.pos.x = nx;
        if (ft_can_move(game,
                        game->player.pos.x, ny))
            game->player.pos.y = ny;
    }

    // S: 後退 (同じ処理で逆方向)
    if (game->keys.s)
    {
        nx = game->player.pos.x
           - game->player.dir.x * MOVE_SPEED;
        ny = game->player.pos.y
           - game->player.dir.y * MOVE_SPEED;
        if (ft_can_move(game, nx,
                        game->player.pos.y))
            game->player.pos.x = nx;
        if (ft_can_move(game,
                        game->player.pos.x, ny))
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

```c title="move.c (rotate)" linenums="1"
// 回転行列を使って向きを変える
static void ft_rotate(t_game *game, double angle)
{
    double old_dir_x;
    double old_plane_x;

    // 古い dir.x を保存
    // (dir.y の更新で dir.x を使うので)
    old_dir_x = game->player.dir.x;

    // 2D 回転行列:
    // | cos  -sin | | x |   | x*cos - y*sin |
    // | sin   cos | | y | = | x*sin + y*cos |
    game->player.dir.x =
        game->player.dir.x * cos(angle)
        - game->player.dir.y * sin(angle);
    game->player.dir.y =
        old_dir_x * sin(angle)
        + game->player.dir.y * cos(angle);

    // カメラプレーンも同じ角度で回転
    // (向きと連動して視野も回る必要がある)
    old_plane_x = game->player.plane.x;
    game->player.plane.x =
        game->player.plane.x * cos(angle)
        - game->player.plane.y * sin(angle);
    game->player.plane.y =
        old_plane_x * sin(angle)
        + game->player.plane.y * cos(angle);
}
```

#### メインの移動関数

```c title="move.c (move)" linenums="1"
void ft_move(t_game *game)
{
    // WASD の判定
    ft_move_forward_back(game);
    ft_move_strafe(game);

    // 矢印キーの判定
    // 負の角度 = 反時計回り (左回転)
    if (game->keys.left)
        ft_rotate(game, -ROT_SPEED);
    // 正の角度 = 時計回り (右回転)
    if (game->keys.right)
        ft_rotate(game, ROT_SPEED);
}
```

### メインループ

```c
// init.c または render.c に書かれる
int ft_loop(t_game *game)
{
    ft_move(game);           // 移動計算
    ft_render(game);         // 画面再描画
    mlx_put_image_to_window( // フレームを画面に転送
        game->mlx, game->win,
        game->frame.ptr, 0, 0);
    return (0);
}

// main でフックを登録
mlx_loop_hook(game.mlx, ft_loop, &game);
mlx_hook(game.win, 2, 1L<<0,
         ft_key_press, &game);
mlx_hook(game.win, 3, 1L<<1,
         ft_key_release, &game);
mlx_hook(game.win, 17, 0,
         ft_close, &game);
mlx_loop(game.mlx);  // 無限ループ開始
```

---

## 4. 評価シートの確認項目

- [ ] W/A/S/D で移動できる
- [ ] ← / → で回転できる
- [ ] ESC で終了する
- [ ] ウィンドウ × ボタンで終了する
- [ ] 壁にめり込まない
- [ ] 斜め移動がスムーズ

---

## 5. テストチェックリスト

- [ ] W を押しっぱなしで連続移動
- [ ] 壁に向かって W を押してもめり込まない
- [ ] 角で W + D を押してスライド移動
- [ ] ← → で回転、視野が変化
- [ ] ESC で即終了、リークなし
- [ ] ウィンドウを × ボタンで閉じて終了

---

## 6. ディフェンスで聞かれること

| 質問 | 答え方 |
|------|--------|
| イベントループとは？ | 何か起きるまで待ち、起きたらコールバック関数を呼ぶ仕組み。miniLibX の `mlx_loop` が裏で回している |
| キー押下を直接処理しない理由は？ | 押しっぱなしで連続移動を実現するため。フラグで状態を持ち、毎フレームチェック |
| 衝突判定の仕組みは？ | 次の位置 (`nx`, `ny`) がマップ範囲内で、かつ `'1'` (壁) でないかチェック |
| X と Y を別々に判定する理由は？ | 壁沿いにスライド移動できるようにするため |
| 回転はどう実装？ | 2D 回転行列を dir と plane の両方に適用 |
| plane を一緒に回す理由は？ | 視野角（FOV）がプレイヤーの向きに追従する必要があるため |
| ESC で即 exit してリークしない？ | `ft_cleanup` を先に呼んでから `exit(0)` するので OK |

---

## 7. よくあるミス

!!! warning "plane の回転忘れ"
    `dir` だけ回して `plane` を忘れると視野が歪む（回すほどおかしくなる）。

!!! warning "`old_dir_x` を使わない"
    `dir.x` を先に更新すると、`dir.y` の式で使う「古い値」が失われる。一時変数に保存が必須。

!!! warning "X と Y を一緒に判定"
    `ft_can_move(nx, ny)` と 1 回で判定すると、角で動けなくなる（スタック感）。

!!! warning "ESC で exit するだけ"
    `cleanup` を呼ばずに `exit` するとメモリリーク。必ず cleanup → exit の順。

---

## 8. 次のページへ

次は [メモリ管理](06-memory.md) で、リークを防ぐ方法を学びます。
