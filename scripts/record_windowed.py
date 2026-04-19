#!/usr/bin/env python3
"""cub3D のウィンドウ ID で直接録画し、PID 指定でキー送信。
screencapture -v -l <windowID> と CGEventPostToPid を組み合わせて、
他ウィンドウの影響を受けずに cub3D の映像 + 操作を取得。"""
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


def get_window_id():
    wins = CGWindowListCopyWindowInfo(
        kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
    for w in wins:
        if "cub3D" in w.get("kCGWindowOwnerName", ""):
            return w.get("kCGWindowNumber")
    return None


def to_gif(mov, gif, fps=15, scale=600):
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
    mov = "/tmp/cub3d_windowed.mov"
    gif = os.path.join(OUT, "gameplay.gif")

    print("🎬 cub3D Window-ID recording")
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
    print(f"PID: {pid}, Window ID: {win_id}")

    # ウィンドウ ID 指定で録画
    duration = 8
    if os.path.exists(mov):
        os.remove(mov)
    rec_proc = subprocess.Popen([
        "screencapture", "-v", f"-V{duration}",
        "-l", str(win_id), "-x", mov,
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.2)

    # PID 直接送信（cub3D がフォーカスを持っていなくても届く）
    print("🎮 Keys: →→→ rotate right")
    hold(pid, KEY_RIGHT, 1.3)
    time.sleep(0.2)
    print("🎮 Keys: W forward")
    hold(pid, KEY_W, 1.0)
    time.sleep(0.2)
    print("🎮 Keys: ←←← rotate left")
    hold(pid, KEY_LEFT, 2.0)
    time.sleep(0.2)
    print("🎮 Keys: S back")
    hold(pid, KEY_S, 0.8)

    rec_proc.wait()
    cub_proc.terminate()
    try:
        cub_proc.wait(timeout=2)
    except Exception:
        cub_proc.kill()

    if os.path.exists(mov):
        print("🎞️  Converting to GIF...")
        to_gif(mov, gif)
        size = os.path.getsize(gif) / 1024
        print(f"✅ Saved: {gif} ({size:.0f}KB)")


if __name__ == "__main__":
    main()
