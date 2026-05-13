# cub3D 評価対策

このページは cub3D の defense（評価面談）に向けた **「評価項目別の早見表・概要・各詳細ページへの入口」** です。

各評価セクションの「英語原文 + 日本語訳 + 評価者が見るコード + 想定質問 + よくある罠 + 提出前チェック」は、それぞれの専用ページにまとめてあります。

---

## このプロジェクトの評価テーマ

> **レイキャスティングの仕組みを理解し、メモリリークなく実装できているか**

---

## 📋 評価セクション別の詳細ページ

| 評価セクション | 内容 | 詳細 |
|:---|:---|:---|
| **Executable name** | `cub3D` 実行ファイル名 / 再リンクなし / コンパイルフラグ | [eval-execution](eval-execution.md) |
| **Configuration file** | NO/SO/EA/WE/F/C/map の読み取り / 不正設定 / `.cub` 拡張子 | [eval-config](eval-config.md) |
| **Technical elements of the display** | ウィンドウ表示 / 隠す・最小化・最大化への対応 | [eval-display](eval-display.md) |
| **User basic events** | × ボタン / ESC / 4 つの移動キー | [eval-events](eval-events.md) |
| **Movements** | N/S/E/W spawn / 矢印回転 / WASD or ZQSD / smooth 表示 | [eval-movement](eval-movement.md) |
| **Walls** | 4 方向テクスチャ / パス変更反映 / 床天井色 | [eval-walls](eval-walls.md) |
| **Error management** | 引数耐性 / メモリリーク / キーボード乱打 / マップ変更 | [eval-errors](eval-errors.md) |
| **Bonus** | 壁衝突 / ミニマップ / ドア / アニメスプライト / マウス回転 | [eval-bonus](eval-bonus.md) |

---

## 評価前チェック（即不合格を避ける）

以下を **1 つでも満たしていなければ、そもそも採点対象外** になる可能性あり。

- [ ] `make` がエラーも警告もなく通る
- [ ] `-Wall -Wextra -Werror` フラグが Makefile にある
- [ ] norminette が通る（NG があると即 0 点の可能性）
- [ ] **メモリリークなし** (`valgrind` / `leaks` で確認)
- [ ] 関数あたり 25 行以内、1 ファイル 5 関数以内（42 norm）

!!! danger "即不合格フラグ"

    | フラグ | 条件 |
    |--------|------|
    | **Invalid compilation** | コンパイルエラー or 警告 |
    | **Norm error** | norminette NG |
    | **Crash** | segfault / 無限ループ |
    | **Leaks** | valgrind / leaks でリーク検出 |
    | **Forbidden function** | 許可されていない関数の使用 |
    | **Can't support / explain code** | アルゴリズムを説明できない |

---

## 評価の流れ（30 分）

```
1. Git リポジトリ確認 (5分)
   ├─ clone してビルド確認
   └─ norminette チェック
        ↓
2. 動作確認 (10分)
   ├─ 正常なマップで実行
   ├─ 操作 (W/A/S/D/矢印/ESC/×)
   └─ 異常系マップでエラー終了
        ↓
3. コードレビュー (10分)
   ├─ レイキャスティング説明
   ├─ パーサーの質問
   └─ メモリ管理の質問
        ↓
4. 評価確定 (5分)
```

---


## 概念の深掘り

### レイキャスティングの全体像

```
+-- プレイヤー視点（上から） --+
|                              |
|  plane                       |
|    +                         |
|    |                         |
|    +-------+   dir           |
|   /|       |    ↑            |
|  / |       |   /             |
| /  |       |  /              |
|/   |       | /               |
|    |   P   |/                |
|    +-------+                 |
|                              |
|   視野 (FOV)                 |
+------------------------------+

画面の各ピクセル x (0..WIN_W) について:
  1. camera_x = 2x/WIN_W - 1  (-1〜+1)
  2. ray.dir = dir + plane * camera_x
  3. DDA で格子を渡って壁にぶつかるまで進む
  4. perp_wall_dist (魚眼補正済み距離) を計算
  5. line_h = WIN_H / perp_wall_dist
  6. 壁を line_h の高さで縦線として描画
     (テクスチャから色を取って 1 ピクセルずつ)
```

### DDA の動きを図で

```
プレイヤーから →方向に光線を飛ばす

 y
 ^
 |  +---+---+---+---+
 |  | 0 | 0 | 0 | 1 |
 |  +---+---+---+---+
 |  | 0 |P→→→→→→→ 1 |
 |  +---+---+---+---+
 |  | 0 | 0 | 0 | 1 |
 |  +---+---+---+---+
 +---------------------------> x

手順:
  step1: X の次の格子線まで 0.4
  step2: Y の次の格子線まで 0.7
    → 小さい方 (X=0.4) に進む
  step3: X の次まで 1.4, Y は 0.7
    → Y に進む
  ...
  hit: map[y][x] == '1' で終了
```

---

## 即不合格フラグ一覧

| フラグ | 意味 |
|--------|------|
| **Crash** | 無効なマップ、配列範囲外、null デリファレンス等でクラッシュ |
| **Leaks** | valgrind / leaks でリーク検出 |
| **Norm error** | 関数 25 行超え、1 ファイル 5 関数超え、禁止構文（for, 複数変数宣言）等 |
| **Forbidden function** | 禁止関数（`printf` 等）の使用 |
| **Cheat** | 他人のコードのコピー |
| **Can't support / explain code** | **レイキャスティング / DDA を説明できない** |
| **Incomplete work** | ESC 終了や × ボタン等の基本操作が動かない |

!!! tip "ディフェンス前の 10 分チェック"
    1. `make re` が警告なく通る
    2. `valgrind ./cub3D maps/valid.cub` でリーク 0
    3. 正常マップで操作 → 違和感なし
    4. 壊れたマップ（プレイヤーなし等）で **エラー終了**
    5. ESC、× ボタンで **リークなく終了**
    6. **レイキャスティングの説明を 3 分で** 口頭で練習

---

## 参考リンク

- [Lode's Computer Graphics Tutorial — Raycasting](https://lodev.org/cgtutor/raycasting.html) — 本家解説
- [42 miniLibX documentation](https://harm-smits.github.io/42docs/libs/minilibx) — API リファレンス
