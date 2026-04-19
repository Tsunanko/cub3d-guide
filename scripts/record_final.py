#!/usr/bin/env python3
"""cub3D デモビルドを 10 秒録画して GIF にする（ループ用・タイトルバー除去）"""
import os
import shutil
import subprocess
import threading
import time

from PIL import Image as PILImage
from Quartz import (
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


def capture(win_id):
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
    img = PILImage.frombytes("RGBA", (w, h), raw, "raw", "BGRA", bpr)
    return img.convert("RGB")


def main():
    os.makedirs(OUT, exist_ok=True)
    gif = os.path.join(OUT, "gameplay.gif")

    print("🎬 cub3D demo recording (10s loop)")
    cub_proc = subprocess.Popen(
        [CUB3D, MAP], cwd=CUB3D_DIR,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3)

    win_id = get_window_id()
    if not win_id:
        print("❌ window not found")
        cub_proc.kill()
        return
    print(f"Window ID: {win_id}")

    # 10秒録画（fps 20 で 200 フレーム程度を目標）
    duration = 10.0
    fps = 20
    interval = 1.0 / fps
    frames = []
    stop = [False]

    def capture_loop():
        start = time.time()
        while not stop[0]:
            t_now = time.time()
            img = capture(win_id)
            if img:
                # タイトルバー (約28px 分) を切り落とす
                # + サイズを 600px 幅にリサイズ（Retinaなのでオリジナル2048幅）
                w, h = img.size
                title_h = int(h * 28 / 796)  # 実ウィンドウ比率で28px
                img = img.crop((0, title_h, w, h))
                img.thumbnail((600, 600), PILImage.LANCZOS)
                frames.append(img)
            elapsed = time.time() - t_now
            remain = interval - elapsed
            if remain > 0:
                time.sleep(remain)
            if time.time() - start >= duration:
                break

    t = threading.Thread(target=capture_loop)
    t.start()
    t.join()
    stop[0] = True

    cub_proc.terminate()
    try:
        cub_proc.wait(timeout=2)
    except Exception:
        cub_proc.kill()

    print(f"Captured {len(frames)} frames")

    if not frames:
        print("❌ no frames")
        return

    # ffmpeg 経由で高品質GIF
    tmp_dir = "/tmp/cub3d_frames_final"
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    os.makedirs(tmp_dir)
    for i, f in enumerate(frames):
        f.save(f"{tmp_dir}/f{i:04d}.png")

    palette = "/tmp/cub3d_palette_final.png"
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
        "-loop", "0",
        gif,
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    shutil.rmtree(tmp_dir)
    if os.path.exists(palette):
        os.remove(palette)

    size = os.path.getsize(gif) / 1024
    print(f"✅ Saved: {gif} ({size:.0f}KB, {len(frames)} frames, {fps}fps)")


if __name__ == "__main__":
    main()
