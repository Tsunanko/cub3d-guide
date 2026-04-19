#!/usr/bin/env python3
"""cub3D を起動して自然な前面表示のまま録画 + CGEventPostToPid でキー送信。
activate() を呼ばずに、cub3D が起動直後に前面になる動作を活用。"""
import os
import subprocess
import time
from Quartz import (
    CGEventCreateKeyboardEvent,
    CGEventPostToPid,
    CGWindowListCopyWindowInfo,
    kCGWindowListOptionOnScreenOnly,
    kCGNullWindowID,
)

CUB3D = "/Users/ichippe/Workspace/01-42tokyo/milestone4/cub3d/cub3D"
CUB3D_DIR = "/Users/ichippe/Workspace/01-42tokyo/milestone4/cub3d"
MAP = "maps/valid/00_subject.cub"
OUT = "/Users/ichippe/Workspace/01-42tokyo/milestone4/cub3d-guide/docs/images"

KEY_W, KEY_S = 13, 1
KEY_LEFT, KEY_RIGHT = 123, 124


def send(pid, key, down):
    ev = CGEventCreateKeyboardEvent(None, key, down)
    CGEventPostToPid(pid, ev)


def hold(pid, key, sec):
    send(pid, key, True)
    time.sleep(sec)
    send(pid, key, False)


def get_bounds():
    wins = CGWindowListCopyWindowInfo(
        kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
    for w in wins:
        if "cub3D" in w.get("kCGWindowOwnerName", ""):
            b = w.get("kCGWindowBounds", {})
            return (int(b["X"]), int(b["Y"]),
                    int(b["Width"]), int(b["Height"]))
    return None


def to_gif(mov, gif, fps=15, scale=640):
    palette = mov + ".palette.png"
    subprocess.run([
        "ffmpeg", "-y", "-i", mov,
        "-vf", f"fps={fps},scale={scale}:-1:flags=lanczos,palettegen",
        palette,
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run([
        "ffmpeg", "-y", "-i", mov, "-i", palette,
        "-lavfi",
        f"fps={fps},scale={scale}:-1:flags=lanczos [x];[x][1:v] paletteuse",
        gif,
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if os.path.exists(palette):
        os.remove(palette)


def main():
    os.makedirs(OUT, exist_ok=True)
    mov = "/tmp/cub3d_passive.mov"
    gif = os.path.join(OUT, "gameplay.gif")

    print("🎬 cub3D passive recording")
    cub_proc = subprocess.Popen(
        [CUB3D, MAP], cwd=CUB3D_DIR,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3)  # ウィンドウ立ち上がりを待つ
    pid = cub_proc.pid

    bounds = get_bounds()
    if not bounds:
        print("❌ window not found")
        cub_proc.kill()
        return
    x, y, w, h = bounds
    print(f"Window: {bounds}")

    # 録画開始
    duration = 7
    rec_proc = subprocess.Popen([
        "screencapture", "-v", f"-V{duration}",
        f"-R{x},{y+28},{w},{h-28}", "-x", mov,
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.2)

    # activate 無し、PID 直接送信
    print("Keys: →→→")
    hold(pid, KEY_RIGHT, 1.5)
    time.sleep(0.1)
    print("Keys: W forward")
    hold(pid, KEY_W, 0.8)
    time.sleep(0.1)
    print("Keys: ←←←")
    hold(pid, KEY_LEFT, 1.5)
    time.sleep(0.1)
    print("Keys: S back")
    hold(pid, KEY_S, 0.6)

    rec_proc.wait()
    cub_proc.terminate()
    try:
        cub_proc.wait(timeout=2)
    except Exception:
        cub_proc.kill()

    if os.path.exists(mov):
        to_gif(mov, gif)
        size = os.path.getsize(gif) / 1024
        print(f"✅ Saved: {gif} ({size:.0f}KB)")


if __name__ == "__main__":
    main()
