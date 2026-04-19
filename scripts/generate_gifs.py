#!/usr/bin/env python3
"""cub3D 教育用 GIF を自動生成するスクリプト。

生成される GIF:
  - raycasting.gif : トップダウン視点での光線投射
  - dda.gif        : DDA アルゴリズムのステップ進行
  - rotation.gif   : プレイヤー回転時の視野変化
  - fisheye.gif    : 魚眼補正の前後比較
"""
import math
import os
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(__file__), "..", "docs", "images")
os.makedirs(OUT, exist_ok=True)

CELL = 64              # マスのピクセル数
GRID = (10, 8)         # (cols, rows)
W, H = CELL * GRID[0], CELL * GRID[1]

COLOR_BG = (245, 245, 250)
COLOR_GRID = (210, 210, 220)
COLOR_WALL = (96, 77, 55)
COLOR_WALL_EDGE = (60, 40, 20)
COLOR_FLOOR = (234, 228, 210)
COLOR_PLAYER = (76, 175, 80)
COLOR_PLAYER_EDGE = (27, 94, 32)
COLOR_RAY = (255, 152, 0, 200)
COLOR_RAY_HIT = (244, 67, 54)
COLOR_TEXT = (40, 40, 50)

MAP = [
    "##########",
    "#........#",
    "#........#",
    "#...##...#",
    "#........#",
    "#........#",
    "#........#",
    "##########",
]


def get_font(size=16):
    for path in [
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
    ]:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def draw_base_map(img, draw, highlight_cell=None, show_grid=True):
    """マップの床/壁/格子を描く。"""
    # Floor
    draw.rectangle([0, 0, W, H], fill=COLOR_BG)
    # Walls + floors
    for y, row in enumerate(MAP):
        for x, ch in enumerate(row):
            rect = [x * CELL, y * CELL, (x + 1) * CELL, (y + 1) * CELL]
            if ch == "#":
                draw.rectangle(rect, fill=COLOR_WALL, outline=COLOR_WALL_EDGE)
            else:
                draw.rectangle(rect, fill=COLOR_FLOOR)
    # Highlight
    if highlight_cell:
        hx, hy = highlight_cell
        draw.rectangle(
            [hx * CELL, hy * CELL, (hx + 1) * CELL, (hy + 1) * CELL],
            outline=(255, 87, 34), width=4,
        )
    # Grid
    if show_grid:
        for i in range(GRID[0] + 1):
            draw.line([(i * CELL, 0), (i * CELL, H)], fill=COLOR_GRID, width=1)
        for i in range(GRID[1] + 1):
            draw.line([(0, i * CELL), (W, i * CELL)], fill=COLOR_GRID, width=1)


def draw_player(draw, px, py, dir_angle, size=14):
    """プレイヤーを円 + 向き矢印で描く。"""
    x = px * CELL
    y = py * CELL
    draw.ellipse([x - size, y - size, x + size, y + size],
                 fill=COLOR_PLAYER, outline=COLOR_PLAYER_EDGE, width=2)
    # Direction arrow
    ex = x + math.cos(dir_angle) * (size + 18)
    ey = y + math.sin(dir_angle) * (size + 18)
    draw.line([(x, y), (ex, ey)], fill=COLOR_PLAYER_EDGE, width=3)


def cast_ray(px, py, angle, max_dist=20.0):
    """DDA で壁までの距離と hit 点を返す。返り値: (hit_x, hit_y, cells_visited)"""
    dx = math.cos(angle)
    dy = math.sin(angle)

    cells = []  # 通過したマス (DDA 可視化用)

    map_x, map_y = int(px), int(py)
    delta_x = abs(1 / dx) if dx != 0 else 1e30
    delta_y = abs(1 / dy) if dy != 0 else 1e30

    if dx < 0:
        step_x = -1
        side_x = (px - map_x) * delta_x
    else:
        step_x = 1
        side_x = (map_x + 1 - px) * delta_x
    if dy < 0:
        step_y = -1
        side_y = (py - map_y) * delta_y
    else:
        step_y = 1
        side_y = (map_y + 1 - py) * delta_y

    cells.append((map_x, map_y))
    for _ in range(200):
        if side_x < side_y:
            side_x += delta_x
            map_x += step_x
            side = 0
            perp = side_x - delta_x
        else:
            side_y += delta_y
            map_y += step_y
            side = 1
            perp = side_y - delta_y

        cells.append((map_x, map_y))
        if map_x < 0 or map_x >= GRID[0] or map_y < 0 or map_y >= GRID[1]:
            break
        if MAP[map_y][map_x] == "#":
            hit_x = px + perp * dx
            hit_y = py + perp * dy
            return hit_x, hit_y, cells, perp, side

    return px + dx * max_dist, py + dy * max_dist, cells, max_dist, -1


def draw_label(draw, text, xy, size=18, color=None):
    font = get_font(size)
    color = color or COLOR_TEXT
    # Background box for readability
    bbox = draw.textbbox(xy, text, font=font)
    draw.rectangle(
        [bbox[0] - 6, bbox[1] - 4, bbox[2] + 6, bbox[3] + 4],
        fill=(255, 255, 255, 220),
    )
    draw.text(xy, text, fill=color, font=font)


# ============================================================
# GIF 1: レイキャスティング基本（プレイヤー回転 + 扇形の光線）
# ============================================================
def gen_raycasting():
    frames = []
    px, py = 2.5, 4.0
    FOV = math.radians(66)
    N_RAYS = 40
    FRAMES = 60

    for f in range(FRAMES):
        angle_base = math.radians(f * (360 / FRAMES))
        img = Image.new("RGB", (W, H), COLOR_BG)
        draw = ImageDraw.Draw(img, "RGBA")
        draw_base_map(img, draw)

        # 扇形のレイ
        for i in range(N_RAYS):
            t = i / (N_RAYS - 1) - 0.5  # -0.5 to +0.5
            a = angle_base + t * FOV
            hx, hy, _, _, _ = cast_ray(px, py, a)
            x0 = px * CELL
            y0 = py * CELL
            x1 = hx * CELL
            y1 = hy * CELL
            draw.line([(x0, y0), (x1, y1)], fill=COLOR_RAY, width=1)

        # プレイヤー
        draw_player(draw, px, py, angle_base)
        draw_label(draw, "Raycasting (Top-down view)", (16, 12))
        draw_label(draw, f"Rays: {N_RAYS}", (16, H - 40))
        frames.append(img.convert("P", palette=Image.ADAPTIVE))

    path = os.path.join(OUT, "raycasting.gif")
    frames[0].save(path, save_all=True, append_images=frames[1:],
                   duration=80, loop=0, optimize=True, disposal=2)
    print(f"[OK] {path}")


# ============================================================
# GIF 2: DDA ステップ（1 マスずつ進む様子）
# ============================================================
def gen_dda():
    px, py = 2.5, 4.5
    angle = math.radians(-25)  # 右上方向
    _, _, cells, _, _ = cast_ray(px, py, angle)
    # 終点に到達したら壁なので、壁のマスで停止
    frames = []

    # 最初に 10 フレームの静止（読者に状況を見せる）
    base_img = Image.new("RGB", (W, H), COLOR_BG)
    base_draw = ImageDraw.Draw(base_img, "RGBA")
    draw_base_map(base_img, base_draw)
    draw_player(base_draw, px, py, angle)
    draw_label(base_draw, "DDA: step through grid cells", (16, 12))
    for _ in range(10):
        frames.append(base_img.convert("P", palette=Image.ADAPTIVE))

    # 1 マスずつ
    for step, (cx, cy) in enumerate(cells):
        img = Image.new("RGB", (W, H), COLOR_BG)
        draw = ImageDraw.Draw(img, "RGBA")
        draw_base_map(img, draw, highlight_cell=(cx, cy))

        # 光線（プレイヤーから現在のセル中心まで）
        x0 = px * CELL
        y0 = py * CELL
        x1 = (cx + 0.5) * CELL
        y1 = (cy + 0.5) * CELL
        draw.line([(x0, y0), (x1, y1)], fill=COLOR_RAY, width=3)

        draw_player(draw, px, py, angle)
        is_wall = 0 <= cy < len(MAP) and 0 <= cx < len(MAP[0]) and MAP[cy][cx] == "#"
        status = f"Step {step+1}: cell ({cx},{cy}) {'= WALL!' if is_wall else ''}"
        draw_label(draw, "DDA: step through grid cells", (16, 12))
        draw_label(draw, status, (16, H - 40),
                   color=(200, 30, 30) if is_wall else COLOR_TEXT)
        dup = 8 if is_wall else 3
        for _ in range(dup):
            frames.append(img.convert("P", palette=Image.ADAPTIVE))
        if is_wall:
            break

    path = os.path.join(OUT, "dda.gif")
    frames[0].save(path, save_all=True, append_images=frames[1:],
                   duration=180, loop=0, optimize=True, disposal=2)
    print(f"[OK] {path}")


# ============================================================
# GIF 3: プレイヤー回転時の視野変化
# ============================================================
def gen_rotation():
    frames = []
    px, py = 5.0, 4.0
    FOV = math.radians(66)
    N_RAYS = 30
    FRAMES = 40

    for f in range(FRAMES):
        # ゆっくり左右に振る（-60度〜+60度）
        angle_base = math.radians(60 * math.sin(f * 2 * math.pi / FRAMES))
        img = Image.new("RGB", (W, H), COLOR_BG)
        draw = ImageDraw.Draw(img, "RGBA")
        draw_base_map(img, draw)

        # 視野の光線
        for i in range(N_RAYS):
            t = i / (N_RAYS - 1) - 0.5
            a = angle_base + t * FOV
            hx, hy, _, _, _ = cast_ray(px, py, a)
            x0 = px * CELL
            y0 = py * CELL
            x1 = hx * CELL
            y1 = hy * CELL
            draw.line([(x0, y0), (x1, y1)], fill=COLOR_RAY, width=1)

        draw_player(draw, px, py, angle_base)
        draw_label(draw, "Player rotation", (16, 12))
        draw_label(draw, f"angle: {math.degrees(angle_base):+.0f}°", (16, H - 40))
        frames.append(img.convert("P", palette=Image.ADAPTIVE))

    path = os.path.join(OUT, "rotation.gif")
    frames[0].save(path, save_all=True, append_images=frames[1:],
                   duration=70, loop=0, optimize=True, disposal=2)
    print(f"[OK] {path}")


# ============================================================
# GIF 4: 魚眼 vs 補正（両方を並べて比較）
# ============================================================
def gen_fisheye():
    # 左: 魚眼あり（普通の距離）、右: 補正済み（垂直距離）
    frames = []
    W_half = W // 2
    FRAMES = 40
    for f in range(FRAMES):
        px, py = 5.0, 4.5
        angle_base = math.radians(30 * math.sin(f * 2 * math.pi / FRAMES))

        img = Image.new("RGB", (W_half * 2, H), (20, 20, 25))
        draw = ImageDraw.Draw(img, "RGBA")

        # 各画面幅分のレイを計算
        N = 80  # 縦線の本数
        fov = math.radians(66)
        for i in range(N):
            camera_x = 2 * i / (N - 1) - 1
            # 光線方向
            a = angle_base + camera_x * (fov / 2)

            hx, hy, _, perp_true, _ = cast_ray(px, py, a)
            # 魚眼あり = 実際の光線長
            dist_raw = math.hypot(hx - px, hy - py)

            # 補正あり = 垂直距離（まっすぐ前方への投影）
            dist_perp = dist_raw * math.cos(camera_x * fov / 2)

            h_raw = min(H - 20, int(H / max(dist_raw, 0.3)))
            h_perp = min(H - 20, int(H / max(dist_perp, 0.3)))

            # 左: 魚眼あり
            x_left = int(i * W_half / N)
            w_col = max(1, W_half // N)
            top = (H - h_raw) // 2
            draw.rectangle([x_left, top, x_left + w_col, top + h_raw],
                           fill=(120, 90, 60))
            # 天井・床
            draw.rectangle([x_left, 0, x_left + w_col, top],
                           fill=(70, 90, 180))
            draw.rectangle([x_left, top + h_raw, x_left + w_col, H],
                           fill=(180, 140, 80))

            # 右: 補正済み
            x_right = W_half + int(i * W_half / N)
            top2 = (H - h_perp) // 2
            draw.rectangle([x_right, top2, x_right + w_col, top2 + h_perp],
                           fill=(120, 90, 60))
            draw.rectangle([x_right, 0, x_right + w_col, top2],
                           fill=(70, 90, 180))
            draw.rectangle([x_right, top2 + h_perp, x_right + w_col, H],
                           fill=(180, 140, 80))

        # ラベル
        draw_label(draw, "WITHOUT fisheye correction", (16, 12),
                   color=(200, 30, 30))
        draw_label(draw, "WITH fisheye correction", (W_half + 16, 12),
                   color=(30, 150, 30))

        # 区切り線
        draw.line([(W_half, 0), (W_half, H)], fill=(255, 255, 255), width=2)

        frames.append(img.convert("P", palette=Image.ADAPTIVE))

    path = os.path.join(OUT, "fisheye.gif")
    frames[0].save(path, save_all=True, append_images=frames[1:],
                   duration=80, loop=0, optimize=True, disposal=2)
    print(f"[OK] {path}")


if __name__ == "__main__":
    gen_raycasting()
    gen_dda()
    gen_rotation()
    gen_fisheye()
    print("\n✅ All GIFs generated in:", OUT)
