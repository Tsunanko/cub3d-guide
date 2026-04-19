# 02. パーサー（.cub ファイルの読み込み）

!!! tip "ページナビ"
    ◀️ 前 **[01. 概要とビルド](01-overview.md)** ・ **次 ▶️ [03. レイキャスティング](03-raycasting.md)**

    **cub3D 全ページ:** [00 概要](index.md) · [01 ビルド](01-overview.md) · [**02 パーサー**](02-parser.md) · [03 レイキャスティング](03-raycasting.md) · [04 レンダリング](04-rendering.md) · [05 入力](05-input.md) · [06 メモリ](06-memory.md) · [🎓 評価対策](eval.md)

---

## このページは何？

**`.cub` ファイルを読んで、ゲームが使える形に変換する処理** を解説します。

ファイルは「人間が読み書きしやすいテキスト」ですが、
ゲームは「プログラムが扱いやすい構造体」が欲しい。
この変換が **パーサー** の仕事です。

```
map.cub (テキスト)
   ↓ [パーサー]
t_config (構造体)
   ↓
[ゲーム開始]
```

---

## 1. このページで学ぶこと

- **パーサー**: ファイルから意味を取り出す処理
- **`.cub` ファイルの形式**: 要素定義 + マップデータ
- **状態機械**: どのセクションを読んでいるか追跡
- **マップ検証**: 閉じた壁、プレイヤー 1 人だけなど

---

## 2. 新しい概念の解説

### パーサーって何？

**テキストを読んで、構造化されたデータに変換する処理**です。

例えば `NO ./textures/north.xpm` という 1 行を、
`config.tex_path[TEX_NO] = "./textures/north.xpm"` に変換します。

コンパイラも同じ仕組み：
ソースコードを読んで AST（抽象構文木）に変換します。

### `.cub` ファイルの形式

```
NO ./textures/north.xpm   ← 北側の壁テクスチャ
SO ./textures/south.xpm   ← 南側
WE ./textures/west.xpm    ← 西側
EA ./textures/east.xpm    ← 東側
F 220,100,0               ← 床の色（RGB）
C 100,100,255             ← 天井の色（RGB）

111111                    ← ここからマップ
100001
10N001                    ← N = 北向きプレイヤー
100001
111111
```

ルール:

1. **要素 6 個が必須**: NO, SO, WE, EA, F, C
2. **マップは最後にくる**（要素の後）
3. **マップの壁は `1`、通路は `0`**
4. **プレイヤーは `N` `S` `E` `W` のいずれか 1 つ**
5. **マップは壁で完全に囲まれていないといけない**

### 状態機械って何？

**「今どの状態か」を覚えながら処理を進める仕組み** です。

```
状態1: 要素を読む (NO, SO, ... を探す)
   ↓ 6 個全部揃った
状態2: マップを読む
   ↓ 空行や EOF まで
状態3: 検証
```

コードでは `config->flags` (ビットフラグ) で追跡しています。

```
flags = 0x00  最初: 何もない
flags = 0x01  NO 読み終わり
flags = 0x03  NO + SO
...
flags = 0x3F  全 6 要素そろった → マップ読み込みへ
```

`0x3F` は 2 進数で `0b111111`（6 個の要素フラグが全部オン）。

---

## 3. コード解説

### プログラムの流れ

```
ft_parse(path, config)
  ↓
ファイルを全部読む (read_file)
  ↓
行ごとに分割 (split_lines)
  ↓
1 行ずつ処理
  ├─ flags 不完全 → 要素として解析
  └─ flags 完全   → マップ開始位置を記録
  ↓
マップを解析 (parse_map)
  ↓
マップを検証 (validate_map)
  ↓
メモリ解放して終了
```

### parse.c（エントリポイント）

```c title="parse.c" linenums="1"
void ft_parse(char *path, t_config *config)
{
    char  *content;
    char  **lines;

    // config をゼロクリア
    // (ゴミ値を防ぐため必須)
    ft_bzero(config, sizeof(t_config));

    // ファイルを全部読み込む
    // → 1 つの文字列として持つ
    content = ft_read_file(path);

    // '\n' で分割して行の配列にする
    lines = ft_split_lines(content);

    // content はもう不要なので解放
    // (lines が新しいメモリにコピーを持ってる)
    free(content);

    // 分割失敗 → 終了
    if (!lines)
        ft_error("Memory allocation failed");

    // エラー時のクリーンアップ用に
    // グローバルコンテキストに登録
    ft_set_errctx(config, lines);

    // 1 行ずつ処理
    ft_process_lines(lines, config);

    // マップの検証 (閉じた壁チェック等)
    ft_validate_map(config);

    // エラーコンテキストをクリア
    ft_set_errctx(NULL, NULL);

    // 行配列を解放
    ft_free_lines(lines);
}
```

### 1 行ずつ処理する部分

```c title="parse.c (process_lines)" linenums="1"
static void ft_process_lines(char **lines, t_config *config)
{
    int i;
    int map_start;

    i = 0;
    map_start = -1;  // マップ開始位置を記録

    while (lines[i])
    {
        // flags != 0x3F = まだ 6 要素揃ってない
        if (config->flags != 0x3F)
        {
            // 空行はスキップ
            if (lines[i][0] != '\0')
                ft_parse_elements(lines[i], config);
        }
        // 6 要素揃った → 次はマップ
        // 最初の非空行がマップの開始
        else if (map_start == -1 && lines[i][0] != '\0')
            map_start = i;
        i++;
    }

    // 要素が揃ってない → エラー
    if (!config->flags || config->flags != 0x3F)
        ft_error("Missing element(s) in configuration");

    // マップが見つからない → エラー
    if (map_start == -1)
        ft_error("No map found in file");

    // マップをパース
    ft_parse_map(lines, map_start, config);
}
```

### マップ検証（parse_validate.c）

この部分が **一番評価で見られる** 部分です。

```c title="parse_validate.c" linenums="1"
// 通行可能な文字か判定
// 0 = 空き、NSEW = プレイヤー位置
static int ft_is_walkable(char c)
{
    return (c == '0' || c == 'N' || c == 'S'
         || c == 'E' || c == 'W');
}

// そのマスが壁で囲まれているか確認
static void ft_check_surrounded(t_config *config,
                                 int y, int x)
{
    // マップの端 → NG (壁じゃない外がある)
    if (y == 0 || y == config->map_h - 1
        || x == 0 || x == config->map_w - 1)
        ft_error(
            "Map is not surrounded by walls");

    // 上下左右に空白 (' ') がある → NG
    // (空白は「壁の外」を意味する)
    if (config->map[y - 1][x] == ' '
        || config->map[y + 1][x] == ' '
        || config->map[y][x - 1] == ' '
        || config->map[y][x + 1] == ' ')
        ft_error(
            "Map is not surrounded by walls");
}

void ft_validate_map(t_config *config)
{
    int y, x, player_count;

    player_count = 0;
    y = 0;
    while (y < config->map_h)
    {
        x = 0;
        while (x < config->map_w)
        {
            // プレイヤー文字を見つけたら登録
            char c = config->map[y][x];
            if (c == 'N' || c == 'S'
                || c == 'E' || c == 'W')
                ft_set_player(
                    config, y, x, &player_count);

            // 通行可能マスは壁で囲まれてる必要
            if (ft_is_walkable(c))
                ft_check_surrounded(
                    config, y, x);
            x++;
        }
        y++;
    }

    // プレイヤーが 0 人 → NG
    if (player_count == 0)
        ft_error(
            "No player start position found");

    // プレイヤーが複数 → NG
    if (player_count > 1)
        ft_error(
            "Multiple player start positions");
}
```

!!! info "なぜ壁検証が必要？"
    もし壁に隙間があると、レイキャスティングで
    光線が **マップの外まで飛んでしまい** 無限ループや
    クラッシュの原因になります。

    事前に「壁で完全に囲まれている」ことを保証することで、
    描画時のバグを防ぎます。

---

## 4. 評価シートの確認項目

- [ ] 要素 6 つ（NO, SO, WE, EA, F, C）すべて読めるか
- [ ] 要素が欠けているとエラーになるか
- [ ] マップに不正文字があるとエラーになるか
- [ ] 壁で囲まれていないマップを拒否するか
- [ ] プレイヤーが 0 人 / 複数人の場合エラーか
- [ ] メモリリークなし

---

## 5. テストチェックリスト

異常系テスト（全部エラーメッセージで正常終了すべき）:

- [ ] 引数なし → Usage 表示
- [ ] 存在しないファイル → エラー
- [ ] 拡張子が `.cub` じゃない → エラー
- [ ] テクスチャファイルが存在しない → エラー
- [ ] 色の値が 255 超え → エラー
- [ ] マップが壁で囲まれていない → エラー
- [ ] プレイヤーが 0 人 → エラー
- [ ] プレイヤーが複数 → エラー
- [ ] 不正文字（`A`, `B` 等）がマップに → エラー
- [ ] 要素のみでマップがない → エラー

---

## 6. ディフェンスで聞かれること

| 質問 | 答え方 |
|------|--------|
| パーサーとは何？ | テキストファイルから意味を取り出して構造体に変換する処理 |
| なぜ `flags` でビット管理？ | 要素 6 個が「全部揃ったか」を 1 つの int で効率よく管理するため |
| マップ検証で何を見ている？ | 壁で囲まれているか、プレイヤーが 1 人だけか、不正文字がないか |
| 空白 (' ') の扱いは？ | 「壁の外」として扱う。通行可能マスの周囲に空白があれば壁不足 |
| なぜ `ft_pad_line` で右埋め？ | 行ごとに幅が違うので、最大幅に揃えて矩形にする（処理を単純化） |
| エラー時のメモリリーク対策は？ | `errctx` でグローバルに登録し、エラー時に cleanup する |

---

## 7. よくあるミス

!!! warning "マップ検証を怠る"
    「動くマップだけ」テストして異常系を見逃すと、評価で **Crash** フラグがつきます。

!!! warning "空白の扱いを間違える"
    マップ中の空白 (` `) は「壁の外」扱い。通行可能マスの隣にあったら壁不足としてエラーに。

!!! warning "プレイヤー文字をマップに残す"
    `N` `S` `E` `W` は位置情報を取り出した後、`0` に置き換える必要があります（レイキャスティングで通行可能マスとして扱うため）。

---

## 8. 次のページへ

次は [レイキャスティング](03-raycasting.md) で、一番の核心である描画アルゴリズムを学びましょう。
