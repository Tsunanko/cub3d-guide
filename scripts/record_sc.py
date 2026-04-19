#!/usr/bin/env python3
"""screencapture -l windowID でフレーム毎にウィンドウを撮って GIF にする。"""
import os
import shutil
import subprocess
import time

from AppKit import NSWorkspace
from Quartz import (
    CGWindowListCopyWindowInfo,
    kCGWindowListOptionOnScreenOnly,
    kCGNullWindowID,
)

CUB3D = "/tmp/cub3D_demo"
CUB3D_DIR = "/Users/ichippe/Workspace/01-42tokyo/milestone4/cub3d"
MAP = "maps/valid/02_small_square.cub"
OUT = "/Users/ichippe/Workspace/01-42tokyo/milestone4/cub3d-guide/docs/images"


def get_window_id():
    wins = CGWindowListCopyWindowInfo(
        kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
    for w in wins:
        if "cub3D" in w.get("kCGWindowOwnerName", ""):
            return w.get("kCGWindowNumber")
    return None


def activate(pid):
    for app in NSWorkspace.sharedWorkspace().runningApplications():
        if app.processIdentifier() == pid:
            app.activateWithOptions_(3)
            return True
    return False


def main():
    os.makedirs(OUT, exist_ok=True)
    gif = os.path.join(OUT, "gameplay.gif")
    tmp_dir = "/tmp/cub3d_sc_frames"
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    os.makedirs(tmp_dir)

    print("🎬 cub3D screencapture recording")
    cub_proc = subprocess.Popen(
        [CUB3D, MAP], cwd=CUB3D_DIR,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3)
    pid = cub_proc.pid

    win_id = get_window_id()
    if not win_id:
        print("❌ window not found")
        cub_proc.kill()
        return
    print(f"Window ID: {win_id}")

    # アクティブ化（初回 + 数回）
    for _ in range(3):
        activate(pid)
        time.sleep(0.3)

    # 10 秒間、0.15 秒おきに screencapture でキャプチャ
    # （フォアグラウンドを保つために毎回 activate）
    duration = 7.0
    interval = 0.1
    n_frames = int(duration / interval)

    print(f"Capturing {n_frames} frames...")
    captured = 0
    for i in range(n_frames):
        # 毎回 activate して focus 維持を試みる
        activate(pid)
        subprocess.run([
            "screencapture", "-l", str(win_id),
            "-t", "png", "-x", f"{tmp_dir}/f{i:04d}.png",
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(f"{tmp_dir}/f{i:04d}.png"):
            captured += 1
        time.sleep(interval)

    cub_proc.terminate()
    try:
        cub_proc.wait(timeout=2)
    except Exception:
        cub_proc.kill()

    print(f"Captured {captured} frames")

    if captured < 10:
        print("❌ too few frames")
        return

    # fps と duration から ffmpeg の framerate を決定
    fps = 1.0 / interval  # 実際の撮影 fps

    palette = "/tmp/cub3d_sc_palette.png"
    subprocess.run([
        "ffmpeg", "-y",
        "-framerate", str(int(fps)),
        "-i", f"{tmp_dir}/f%04d.png",
        "-vf", "scale=720:-1:flags=lanczos,palettegen=max_colors=96",
        palette,
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run([
        "ffmpeg", "-y",
        "-framerate", str(int(fps)),
        "-i", f"{tmp_dir}/f%04d.png",
        "-i", palette,
        "-lavfi", "scale=720:-1:flags=lanczos [x]; [x][1:v] paletteuse=dither=bayer:bayer_scale=4",
        "-loop", "0",
        gif,
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    shutil.rmtree(tmp_dir)
    if os.path.exists(palette):
        os.remove(palette)

    size = os.path.getsize(gif) / 1024
    print(f"✅ Saved: {gif} ({size:.0f}KB, ~{fps:.0f}fps)")


if __name__ == "__main__":
    main()
