#!/usr/bin/env python3
"""cub3D を実行して、ffmpeg で画面録画 + CGEvent でキー入力シミュレート。

使い方:
    python3 record_gameplay.py
"""
import os
import subprocess
import time
from Quartz import (
    CGEventCreateKeyboardEvent,
    CGEventPost,
    kCGHIDEventTap,
    CGWindowListCopyWindowInfo,
    kCGWindowListOptionOnScreenOnly,
    kCGNullWindowID,
)
from AppKit import NSWorkspace, NSRunningApplication

CUB3D_DIR = "/Users/ichippe/Workspace/01-42tokyo/milestone4/cub3d"
MAP = "maps/valid/00_subject.cub"
OUT_DIR = "/Users/ichippe/Workspace/01-42tokyo/milestone4/cub3d-guide/docs/images"

# macOS キーコード
KEY_W = 13
KEY_A = 0
KEY_S = 1
KEY_D = 2
KEY_LEFT = 123
KEY_RIGHT = 124


def key_event(keycode, down):
    ev = CGEventCreateKeyboardEvent(None, keycode, down)
    CGEventPost(kCGHIDEventTap, ev)


def press_and_hold(keycode, duration):
    key_event(keycode, True)
    time.sleep(duration)
    key_event(keycode, False)


def get_cub3d_window():
    wins = CGWindowListCopyWindowInfo(
        kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
    for w in wins:
        if "cub3D" in w.get("kCGWindowOwnerName", ""):
            b = w.get("kCGWindowBounds", {})
            return (int(b["X"]), int(b["Y"]),
                    int(b["Width"]), int(b["Height"]))
    return None


def record_gameplay(output_mov, duration=6.0):
    """cub3D を起動して録画、その間にキー入力でカメラを動かす。"""
    # cub3D 起動
    cub_proc = subprocess.Popen(
        [os.path.join(CUB3D_DIR, "cub3D"), MAP],
        cwd=CUB3D_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(3)  # ウィンドウ表示待ち

    # ウィンドウ位置取得
    bounds = get_cub3d_window()
    if not bounds:
        print("❌ cub3D window not found")
        cub_proc.kill()
        return False
    x, y, w, h = bounds
    # タイトルバー分を除く
    title_h = 28
    cap_x = x
    cap_y = y + title_h
    cap_w = w
    cap_h = h - title_h
    print(f"Recording region: {cap_x},{cap_y} {cap_w}x{cap_h}")

    # screencapture で録画開始 (macOS純正)
    # -v 動画 -V 秒数 -R 領域 -x 音なし
    if os.path.exists(output_mov):
        os.remove(output_mov)
    ff_proc = subprocess.Popen([
        "screencapture",
        "-v",
        f"-V{int(duration)}",
        f"-R{cap_x},{cap_y},{cap_w},{cap_h}",
        "-x",
        output_mov,
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    time.sleep(1.0)
    # cub3D をアクティブ化（フォーカス）
    for app in NSWorkspace.sharedWorkspace().runningApplications():
        if app.processIdentifier() == cub_proc.pid:
            app.activateWithOptions_(3)  # ActivateAllWindows | IgnoringOtherApps
            print(f"Activated cub3D (PID {cub_proc.pid})")
            break
    time.sleep(0.5)
    # キー入力シーケンス
    # 右回転
    press_and_hold(KEY_RIGHT, 1.0)
    time.sleep(0.2)
    # 前進
    press_and_hold(KEY_W, 1.2)
    time.sleep(0.2)
    # 左回転
    press_and_hold(KEY_LEFT, 1.0)
    time.sleep(0.2)
    # 後退
    press_and_hold(KEY_S, 1.0)

    ff_proc.wait()
    cub_proc.terminate()
    try:
        cub_proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        cub_proc.kill()
    return True


def mov_to_gif(mov_path, gif_path, fps=12, scale=640):
    """mov を gif に変換（palette 生成で高品質）。"""
    palette = mov_path + ".palette.png"
    subprocess.run([
        "ffmpeg", "-y",
        "-i", mov_path,
        "-vf", f"fps={fps},scale={scale}:-1:flags=lanczos,palettegen",
        palette,
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run([
        "ffmpeg", "-y",
        "-i", mov_path,
        "-i", palette,
        "-lavfi", f"fps={fps},scale={scale}:-1:flags=lanczos [x]; [x][1:v] paletteuse",
        gif_path,
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(palette)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    mov = "/tmp/cub3d_gameplay.mov"
    gif = os.path.join(OUT_DIR, "gameplay.gif")

    print("🎬 Recording gameplay...")
    if record_gameplay(mov, duration=6.0):
        print("🎞️  Converting to GIF...")
        mov_to_gif(mov, gif, fps=12, scale=640)
        size = os.path.getsize(gif) / 1024
        print(f"✅ Saved: {gif} ({size:.0f}KB)")
    else:
        print("❌ Recording failed")


if __name__ == "__main__":
    main()
