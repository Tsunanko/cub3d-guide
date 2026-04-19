#!/usr/bin/env python3
"""CGWindowListCreateImage でウィンドウ内容を直接フレームキャプチャ。
他ウィンドウの前後関係に影響されず cub3D だけを撮影する。"""
import os
import subprocess
import time
from Quartz import (
    CGEventCreateKeyboardEvent,
    CGEventPostToPid,
    CGWindowListCopyWindowInfo,
    CGWindowListCreateImage,
    CGRectNull,
    kCGWindowListOptionOnScreenOnly,
    kCGWindowListOptionIncludingWindow,
    kCGNullWindowID,
    kCGWindowImageBoundsIgnoreFraming,
    kCGWindowImageBestResolution,
    CGImageGetWidth,
    CGImageGetHeight,
    CGImageGetBytesPerRow,
    CGImageGetDataProvider,
    CGDataProviderCopyData,
)
from PIL import Image as PILImage

CUB3D = "/tmp/cub3D_demo"  # デモ版（自動回転+前進）
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


def capture_window(win_id):
    """ウィンドウ単体を PIL Image として取得。"""
    img_ref = CGWindowListCreateImage(
        CGRectNull,
        kCGWindowListOptionIncludingWindow,
        win_id,
        kCGWindowImageBoundsIgnoreFraming | kCGWindowImageBestResolution,
    )
    if img_ref is None:
        return None

    w = CGImageGetWidth(img_ref)
    h = CGImageGetHeight(img_ref)
    bpr = CGImageGetBytesPerRow(img_ref)
    provider = CGImageGetDataProvider(img_ref)
    data = CGDataProviderCopyData(provider)
    raw = bytes(data)

    # BGRA -> RGB (PIL は RGB 順で欲しい)
    img = PILImage.frombytes("RGBA", (w, h), raw, "raw", "BGRA", bpr)
    return img.convert("RGB")


def main():
    os.makedirs(OUT, exist_ok=True)
    gif = os.path.join(OUT, "gameplay.gif")

    print("🎬 cub3D CGImage recording")
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

    # キー送信を別スレッドで
    import threading

    frames = []
    stop = [False]
    fps = 12
    interval = 1.0 / fps

    def capture_loop():
        start = time.time()
        while not stop[0]:
            t_now = time.time()
            img = capture_window(win_id)
            if img:
                # 縮小して軽くする
                img.thumbnail((600, 600 * 3 // 4), PILImage.LANCZOS)
                frames.append(img)
            # fps 維持
            elapsed = time.time() - t_now
            remain = interval - elapsed
            if remain > 0:
                time.sleep(remain)
        print(f"Captured {len(frames)} frames in {time.time()-start:.1f}s")

    t = threading.Thread(target=capture_loop)
    t.start()

    time.sleep(0.5)

    # キー操作シーケンス
    print("🎮 Keys: →→→ rotate right")
    hold(pid, KEY_RIGHT, 1.3)
    time.sleep(0.2)
    print("🎮 Keys: W forward")
    hold(pid, KEY_W, 0.8)
    time.sleep(0.2)
    print("🎮 Keys: ←←← rotate left")
    hold(pid, KEY_LEFT, 2.0)
    time.sleep(0.2)
    print("🎮 Keys: S back")
    hold(pid, KEY_S, 0.6)
    time.sleep(0.3)

    stop[0] = True
    t.join()

    cub_proc.terminate()
    try:
        cub_proc.wait(timeout=2)
    except Exception:
        cub_proc.kill()

    if frames:
        print(f"🎞️  Creating GIF from {len(frames)} frames...")
        # mov経由で高品質GIFを作る
        mov = "/tmp/cub3d_frames.mov"
        # まずPNG連番で保存
        tmp_dir = "/tmp/cub3d_frames"
        os.makedirs(tmp_dir, exist_ok=True)
        for i, f in enumerate(frames):
            f.save(f"{tmp_dir}/f{i:04d}.png")
        # ffmpeg でGIF作成
        palette = "/tmp/cub3d_palette.png"
        subprocess.run([
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", f"{tmp_dir}/f%04d.png",
            "-vf", "palettegen=max_colors=128",
            palette,
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run([
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", f"{tmp_dir}/f%04d.png",
            "-i", palette,
            "-lavfi", "paletteuse=dither=bayer:bayer_scale=3",
            gif,
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # 掃除
        import shutil
        shutil.rmtree(tmp_dir)
        if os.path.exists(palette):
            os.remove(palette)
        size = os.path.getsize(gif) / 1024
        print(f"✅ Saved: {gif} ({size:.0f}KB)")


if __name__ == "__main__":
    main()
