#!/usr/bin/env python3
"""cub3D 起動直後にフォーカスを確保してキー送信しながら録画する。"""
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
from AppKit import NSWorkspace

CUB3D = "/Users/ichippe/Workspace/01-42tokyo/milestone4/cub3d/cub3D"
CUB3D_DIR = "/Users/ichippe/Workspace/01-42tokyo/milestone4/cub3d"
MAP = "maps/valid/00_subject.cub"
OUT = "/Users/ichippe/Workspace/01-42tokyo/milestone4/cub3d-guide/docs/images"

KEY_W, KEY_A, KEY_S, KEY_D = 13, 0, 1, 2
KEY_LEFT, KEY_RIGHT = 123, 124


def send(pid, key, down):
    ev = CGEventCreateKeyboardEvent(None, key, down)
    CGEventPostToPid(pid, ev)


def hold(pid, key, sec):
    send(pid, key, True)
    time.sleep(sec)
    send(pid, key, False)


def activate(pid):
    for app in NSWorkspace.sharedWorkspace().runningApplications():
        if app.processIdentifier() == pid:
            app.activateWithOptions_(3)
            return True
    return False


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
    print("🎬 cub3D 自動録画（触らないでください）")
    print("")
    os.makedirs(OUT, exist_ok=True)
    mov = "/tmp/cub3d_auto.mov"
    gif = os.path.join(OUT, "gameplay.gif")

    # cub3D 起動
    print("1. cub3D 起動中...")
    cub_proc = subprocess.Popen(
        [CUB3D, MAP], cwd=CUB3D_DIR,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2.5)
    pid = cub_proc.pid
    print(f"   PID: {pid}")

    # ウィンドウ位置取得
    bounds = get_bounds()
    if not bounds:
        print("❌ window not found")
        cub_proc.kill()
        return
    x, y, w, h = bounds
    print(f"   Window: {bounds}")

    # 前面化（複数回試す）
    print("2. 前面化...")
    for _ in range(3):
        activate(pid)
        time.sleep(0.3)

    # 録画開始（バックグラウンド）
    duration = 8
    print(f"3. 録画開始 ({duration}秒)")
    rec_proc = subprocess.Popen([
        "screencapture", "-v", f"-V{duration}",
        f"-R{x},{y+28},{w},{h-28}", "-x", mov,
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # 録画が始まるまで少し待つ
    time.sleep(1.5)

    # 再度アクティブ化（録画開始前の安定化後）
    activate(pid)
    time.sleep(0.3)

    # キー送信シーケンス
    print("4. 操作シミュレーション...")
    print("   → 右回転")
    hold(pid, KEY_RIGHT, 1.0)
    time.sleep(0.2)

    activate(pid)
    print("   → 前進")
    hold(pid, KEY_W, 1.0)
    time.sleep(0.2)

    activate(pid)
    print("   → 左回転")
    hold(pid, KEY_LEFT, 1.5)
    time.sleep(0.2)

    activate(pid)
    print("   → 後退")
    hold(pid, KEY_S, 0.8)

    # 録画完了待ち
    rec_proc.wait()
    print("5. 録画完了")

    # cub3D 停止
    cub_proc.terminate()
    try:
        cub_proc.wait(timeout=2)
    except Exception:
        cub_proc.kill()

    # GIF 変換
    if os.path.exists(mov):
        print("6. GIF 変換中...")
        to_gif(mov, gif)
        size = os.path.getsize(gif) / 1024
        print(f"✅ Saved: {gif} ({size:.0f}KB)")


if __name__ == "__main__":
    main()
