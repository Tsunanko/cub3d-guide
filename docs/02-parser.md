# 02. パーサー — `.cub` ファイルの読み込み

!!! tip "ページナビ"
    ◀️ 前 **[01. 概要とビルド](01-overview.md)** ・ **次 ▶️ [03. レイキャスティングとは](03-raycasting.md)**
    ・ **[📚 用語集](glossary.md)**

---

## このページは何？

**`.cub` ファイル（マップ設計図）をプログラムが使える形に変換する処理** を解説します。

- **入力**: テキストファイル（人間が書きやすい）
- **出力**: 構造体（プログラムが扱いやすい）

この変換をする人（プログラム）が **パーサー (parser)** です。

---

## 1. まず知っておきたいこと

### `.cub` ファイルって何？

**cub3D 専用のマップ設計図ファイル** です。

テキストファイル（`.txt` と中身の形式は同じ）ですが、
**決まった書き方のルール** に従って書く必要があります。

=== "📄 `.cub` ファイルの中身の例"

    ```
    NO ./textures/north.xpm    ← 北向きの壁に貼る画像
    SO ./textures/south.xpm    ← 南向きの壁
    WE ./textures/west.xpm     ← 西向きの壁
    EA ./textures/east.xpm     ← 東向きの壁
    F 220,100,0                ← 床の色（RGB）
    C 100,100,255              ← 天井の色（RGB）

    1 1 1 1 1 1                ← ここからマップ
    1 0 0 0 0 1                ← 1 = 壁、0 = 通路
    1 0 N 0 0 1                ← N = 北向きプレイヤー開始位置
    1 0 0 0 0 1
    1 1 1 1 1 1
    ```

=== "🎮 この .cub を読むと…"

    ゲームが起動して、**壁に 4 方向のテクスチャが貼られた 3D 迷路** が
    プレイヤー視点で表示されます。

!!! info "「cub」の由来"
    **cub** は **cube**（立方体）の略。3D 迷路を立方体ブロックで構成している
    イメージから来ています。

### 構造体 (struct) って何？

**「関連する値をまとめて 1 つの箱にする仕組み」** です。

例えば「`.cub` ファイルの情報」は:

- 4 つのテクスチャのパス
- 床の色
- 天井の色
- マップ

…など **複数の情報の集合体**。これを **バラバラの変数** で持つと管理が大変。
**構造体** に入れれば「`config`」という 1 つの箱で全部扱えます。

```c
// cub3D の config 構造体（簡略版）
typedef struct s_config {
    char    *tex_path[4];     // テクスチャパス × 4
    t_color  floor;            // 床の色
    t_color  ceiling;          // 天井の色
    char   **map;              // マップ（二次元配列）
    int      map_w;            // マップの幅
    int      map_h;            // マップの高さ
    int      flags;            // どの要素を読んだかの印
} t_config;
```

!!! info "引き出し付き整理箱のイメージ"
    構造体 = 複数の引き出しが付いた整理箱。
    各引き出し（メンバ）に違う情報を入れて、まとめて持ち運べます。

---

## 2. パーサーって何？

**テキストを読んで、構造化されたデータ（構造体）に変換する処理** です。

```mermaid
flowchart LR
    A[📄 .cub ファイル<br>テキスト] --> B[🔧 パーサー]
    B --> C[📦 config 構造体<br>プログラム用]
    C --> D[🎮 ゲーム開始]

    style A fill:#FFF9C4
    style B fill:#BBDEFB
    style C fill:#C8E6C9
    style D fill:#F8BBD0
```

**身近な例**: Excel が CSV を開いてセルに値を入れる処理もパーサーです。

---

## 3. `.cub` ファイルのルール

| ルール | 内容 |
|:---|:---|
| ① 要素 6 個が必須 | NO, SO, WE, EA, F, C（順番は自由） |
| ② マップは最後 | 6 要素を全部読んだ後に書く |
| ③ 壁は `1`、通路は `0` | それ以外の文字は不正 |
| ④ プレイヤーは `N` `S` `E` `W` のいずれか 1 つだけ | 0 人・複数人は不正 |
| ⑤ マップは壁で完全に囲む | 隙間や空白で囲い忘れは不正 |

### 6 つの必須要素

| 記号 | 英語 | 日本語 | 値の例 |
|:-:|:---|:---|:---|
| **NO** | North texture | 北側の壁画像 | `NO ./textures/north.xpm` |
| **SO** | South texture | 南側の壁画像 | `SO ./textures/south.xpm` |
| **WE** | West texture | 西側の壁画像 | `WE ./textures/west.xpm` |
| **EA** | East texture | 東側の壁画像 | `EA ./textures/east.xpm` |
| **F** | Floor color | 床の色 (RGB) | `F 220,100,0` |
| **C** | Ceiling color | 天井の色 (RGB) | `C 100,100,255` |

### マップの記号

| 記号 | 意味 | 英語名 |
|:-:|:---|:---|
| `1` | 壁（通れない） | Wall |
| `0` | 通路（通れる） | Floor / Path |
| `N` | プレイヤー開始位置・北向き | North |
| `S` | プレイヤー開始位置・南向き | South |
| `E` | プレイヤー開始位置・東向き | East |
| `W` | プレイヤー開始位置・西向き | West |
| 空白 | マップの外 | Outside |

---

## 4. config flags（設定フラグ）って何？

**「.cub の要素 6 個のうち、どれをもう読んだか」を覚えておく変数** です。

6 個の要素それぞれに **ビット** を割り当て、読み込んだらそのビットを 1 に立てます。

### ビットの対応

| ビット | 2進数 | 16進数 | 意味 |
|:-:|:-:|:-:|:---|
| ビット 0 | `000001` | `0x01` | NO 読んだ |
| ビット 1 | `000010` | `0x02` | SO 読んだ |
| ビット 2 | `000100` | `0x04` | WE 読んだ |
| ビット 3 | `001000` | `0x08` | EA 読んだ |
| ビット 4 | `010000` | `0x10` | F 読んだ |
| ビット 5 | `100000` | `0x20` | C 読んだ |

全部読むと合計 `111111` → **`0x3F`**（10 進数で 63）になります。

```mermaid
flowchart LR
    Start[flags = 0x00<br>何も読んでない] --> R1[NO を読む<br>flags = 0x01]
    R1 --> R2[SO を読む<br>flags = 0x03]
    R2 --> Dots[... 残り 4 つも<br>順次読む]
    Dots --> Full[flags = 0x3F<br>全部完了!]
    Full --> Go[マップ読み取りへ]

    style Start fill:#FFCDD2
    style Full fill:#C8E6C9
    style Go fill:#81C784,color:#fff
```

!!! info "なぜビットで管理？"
    `int` 1 個で 6 個のフラグを同時に管理できて効率的だから。
    `bool tex_no_read; bool tex_so_read; ...` と 6 個作るより簡潔。

---

## 5. 状態機械 (state machine) って何？

**「今どの状態か」を覚えながら処理を進める仕組み**。

cub3D のパーサーは **2 つの状態** を行き来します:

```mermaid
stateDiagram-v2
    [*] --> 要素読取中: パーサー開始
    要素読取中 --> 要素読取中: NO/SO/WE/EA/F/C のいずれかを読む
    要素読取中 --> マップ読取中: flags が 0x3F になった
    マップ読取中 --> マップ読取中: マップ行を読む
    マップ読取中 --> [*]: 空行 or EOF
```

「機械 (machine)」という漢字は **合っています**（state **machine** の直訳）。
**「状態の切り替えをする装置」** というイメージ。

---

## 6. パーサーの動き（ステップごと）

```mermaid
flowchart TD
    Start([ft_parse 開始]) --> ReadFile[ファイル全体を<br>文字列として読み込む]
    ReadFile --> Split[改行で分割して<br>行の配列にする]
    Split --> Loop[1 行ずつ処理]
    Loop --> Check{flags == 0x3F?}
    Check -- No 要素読取中 --> ParseElem[要素として解析<br>NO/SO/WE/EA/F/C]
    ParseElem --> Loop
    Check -- Yes マップ読取中 --> MapStart[マップ開始位置を記録]
    MapStart --> Loop
    Loop --> Finish{全行処理終わり?}
    Finish -- No --> Loop
    Finish -- Yes --> ParseMap[マップを二次元配列に]
    ParseMap --> Validate[マップを検証<br>壁で囲まれてる?<br>プレイヤー 1 人?]
    Validate --> End([パース完了])

    style Start fill:#E3F2FD
    style End fill:#C8E6C9
    style Validate fill:#FFF9C4
```

---

## 7. マップ検証（validation）の詳細

**パースした後、マップが正しいかチェック** します。
ここが評価で最も試される部分です。

### エラーパターン一覧

=== "🟢 OK なマップ"

    ```
    1 1 1 1 1
    1 0 0 0 1
    1 0 N 0 1
    1 1 1 1 1
    ```

    壁で完全に囲まれている。

=== "🔴 NG: 開いた壁"

    ```
    1 1 1 1 1
    1 0 0 0 1
    1 0 N 0 1
    1 1 0 1 1   ← 下が '0' で開いている
    ```

    通路マスから外が見える → エラー "Map is not surrounded by walls"

=== "🔴 NG: プレイヤーなし"

    ```
    1 1 1 1 1
    1 0 0 0 1
    1 0 0 0 1
    1 1 1 1 1
    ```

    N/S/E/W が 1 つもない → エラー "No player start position found"

=== "🔴 NG: プレイヤー複数"

    ```
    1 1 1 1 1
    1 N 0 S 1   ← N と S の 2 人
    1 1 1 1 1
    ```

    プレイヤーが 2 人以上 → エラー "Multiple player start positions"

=== "🔴 NG: 不正文字"

    ```
    1 1 1 1 1
    1 0 X 0 1   ← X は未定義文字
    1 1 1 1 1
    ```

    `X` は不正 → エラー "Invalid character in map"

=== "🔴 NG: 巨大マップ"

    ```
    1 1 1 ... (501 マス以上)
    ```

    500 x 500 を超える → エラー "Map too large"

---

## 8. コード解説（簡潔版）

### エントリポイント

```c title="parse.c (ft_parse)" linenums="1"
void ft_parse(char *path, t_config *config)
{
    char  *content;
    char **lines;

    // ── 準備 ──
    // config をゼロクリア (ゴミ値を防ぐ)
    ft_bzero(config, sizeof(t_config));

    // ファイル全体を1つの文字列として読み込み
    content = ft_read_file(path);

    // 改行で分割して行の配列にする
    lines = ft_split_lines(content);
    free(content);  // 元文字列はもう不要

    if (!lines)
        ft_error("Memory allocation failed");

    // エラー時クリーンアップ用の登録
    ft_set_errctx(config, lines);

    // ── 本処理 ──
    ft_process_lines(lines, config);  // 1 行ずつ処理
    ft_validate_map(config);           // マップの検証

    // ── 後片付け ──
    ft_set_errctx(NULL, NULL);
    ft_free_lines(lines);
}
```

---

## 9. 評価シートの確認項目

- [ ] 要素 6 つすべて読めるか
- [ ] 要素が欠けるとエラーになるか
- [ ] マップに不正文字があるとエラーか
- [ ] 壁で囲まれていないマップを拒否するか
- [ ] プレイヤー 0 人 / 複数人でエラーか
- [ ] メモリリークなし

---

## 10. ディフェンスで聞かれること

| 質問 | 答え方 |
|:---|:---|
| パーサーとは？ | テキストから意味を取り出して構造体に変換する処理 |
| なぜ flags をビットで管理？ | 6 個の要素が全部揃ったか `int` 1 個で効率的に追跡するため |
| マップ検証で何を見る？ | 壁で囲まれてるか、プレイヤーが 1 人だけか、不正文字なし |
| 空白の扱いは？ | 「壁の外」扱い。通路マスの隣に空白があれば壁不足 |
| エラー時のリーク対策は？ | errctx でグローバル登録、`ft_error` から cleanup を呼ぶ |

---

## 11. よくあるミス

!!! warning "マップ検証を怠る"
    正常マップだけテストして異常系を見逃すと **Crash フラグ** の危険。

!!! warning "空白の扱い"
    マップ中の `' '` (空白) は **「壁の外」**。通路マスの隣にあったら壁不足。

!!! warning "プレイヤー文字の後処理"
    `N S E W` は位置情報を取り出した後、`0` に置き換える必要あり。
    そのままだとレイキャスティングで通行判定に影響。

---

## 📚 分からない用語は？

**→ [📚 用語集](glossary.md)** で全用語を平易に解説しています。

---

## 12. 次のページへ

次は [🔦 03. レイキャスティングとは](03-raycasting.md) で、
パースしたマップを **どう 3D に描画するか** を学びます。
