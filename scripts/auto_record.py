#!/usr/bin/env python3
"""cub3D を自動再生して GIF に録画する（複数の戦略を試行）。"""
import os
import subprocess
import time
from Quartz import (
    CGEventCreateKeyboardEvent,
    CGEventPost,
    CGEventPostToPid,
    kCGHIDEventTap,
    CGWindowListCopyWindowInfo,
    kCGWindowListOptionOnScreenOnly,
    kCGNullWindowID,
)
from AppKit import NSWorkspace

CUB3D = "/Users/ichippe/Workspace/01-42tokyo/milestone4/cub3d/cub3D"
CUB3D_DIR = "/Users/ichippe/Workspace/01-42tokyo/milestone4/cub3d"
MAP = "maps/valid/00_subject.cub"

KEY_W, KEY_A, KEY_S, KEY_D = 13, 0, 1, 2
KEY_LEFT, KEY_RIGHT = 123, 124


def post_to_pid(pid, keycode, down):
    ev = CGEventCreateKeyboardEvent(None, keycode, down)
    CGEventPostToPid(pid, ev)


def post_global(keycode, down):
    ev = CGEventCreateKeyboardEvent(None, keycode, down)
    CGEventPost(kCGHIDEventTap, ev)


def hold_pid(pid, keycode, duration):
    post_to_pid(pid, keycode, True)
    time.sleep(duration)
    post_to_pid(pid, keycode, False)


def hold_global(keycode, duration):
    post_global(keycode, True)
    time.sleep(duration)
    post_global(keycode, False)


def activate(pid):
    for app in NSWorkspace.sharedWorkspace().runningApplications():
        if app.processIdentifier() == pid:
            # NSApplicationActivateAllWindows | IgnoringOtherApps
            app.activateWithOptions_(3)
            return True
    return False


def start_cub3d():
    proc = subprocess.Popen(
        [CUB3D, MAP], cwd=CUB3D_DIR,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3)
    return proc


def get_bounds():
    wins = CGWindowListCopyWindowInfo(
        kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
    for w in wins:
        if "cub3D" in w.get("kCGWindowOwnerName", ""):
            b = w.get("kCGWindowBounds", {})
            return (int(b["X"]), int(b["Y"]),
                    int(b["Width"]), int(b["Height"]))
    return None


def start_recording(output_mov, bounds, duration):
    x, y, w, h = bounds
    y += 28  # title bar
    h -= 28
    proc = subprocess.Popen([
        "screencapture", "-v", f"-V{int(duration)}",
        f"-R{x},{y},{w},{h}", "-x", output_mov,
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return proc


def to_gif(mov, gif, fps=12, scale=640):
    palette = mov + ".palette.png"
    subprocess.run([
        "ffmpeg", "-y", "-i", mov,
        "-vf", f"fps={fps},scale={scale}:-1:flags=lanczos,palettegen",
        palette,
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run([
        "ffmpeg", "-y", "-i", mov, "-i", palette,
        "-lavfi",
        f"fps={fps},scale={scale}:-1:flags=lanczos [x]; [x][1:v] paletteuse",
        gif,
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if os.path.exists(palette):
        os.remove(palette)


def try_strategy_1_pid(proc, duration=6):
    """PID 直接送信"""
    mov = "/tmp/cub3d_pid.mov"
    bounds = get_bounds()
    activate(proc.pid)
    time.sleep(0.5)
    start_recording(mov, bounds, duration)
    time.sleep(1.0)

    # 回転 → 前進 → 逆回転 → 後退
    hold_pid(proc.pid, KEY_RIGHT, 0.8)
    time.sleep(0.1)
    hold_pid(proc.pid, KEY_W, 1.0)
    time.sleep(0.1)
    hold_pid(proc.pid, KEY_LEFT, 0.8)
    time.sleep(0.1)
    hold_pid(proc.pid, KEY_S, 0.8)

    time.sleep(duration)
    return mov


def try_strategy_2_global(proc, duration=6):
    """グローバル送信（cub3Dが前面の前提）"""
    mov = "/tmp/cub3d_global.mov"
    bounds = get_bounds()
    activate(proc.pid)
    time.sleep(1.0)
    start_recording(mov, bounds, duration)
    time.sleep(1.0)
    # 再度アクティブ化
    activate(proc.pid)
    time.sleep(0.3)

    hold_global(KEY_RIGHT, 0.8)
    time.sleep(0.1)
    hold_global(KEY_W, 1.0)
    time.sleep(0.1)
    hold_global(KEY_LEFT, 0.8)
    time.sleep(0.1)
    hold_global(KEY_S, 0.8)

    time.sleep(duration)
    return mov


def main():
    out_dir = "/Users/ichippe/Workspace/01-42tokyo/milestone4/cub3d-guide/docs/images"
    os.makedirs(out_dir, exist_ok=True)

    for strategy_name, strategy_fn in [
        ("pid", try_strategy_1_pid),
        ("global", try_strategy_2_global),
    ]:
        print(f"\n▶️ Strategy: {strategy_name}")
        proc = start_cub3d()
        bounds = get_bounds()
        if not bounds:
            print("  ❌ cub3D window not found")
            proc.kill()
            continue
        print(f"  Window bounds: {bounds}")

        try:
            mov = strategy_fn(proc)
            gif = os.path.join(out_dir, f"gameplay_{strategy_name}.gif")
            if os.path.exists(mov):
                to_gif(mov, gif)
                size = os.path.getsize(gif) / 1024
                print(f"  ✅ Saved: {gif} ({size:.0f}KB)")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except Exception:
                proc.kill()
            time.sleep(1)


if __name__ == "__main__":
    main()
