#!/usr/bin/env bash
# cub3D を起動 → 6秒録画 → GIF に変換
# ユーザーが録画中に WASD / 矢印キーで操作する

set -e

CUB3D_DIR="/Users/ichippe/Workspace/01-42tokyo/milestone4/cub3d"
MAP="maps/valid/00_subject.cub"
OUT_DIR="/Users/ichippe/Workspace/01-42tokyo/milestone4/cub3d-guide/docs/images"
DURATION=6

echo "🎬 cub3D gameplay 録画スクリプト"
echo "────────────────────────────────────"
echo "cub3D が起動したら、録画の ${DURATION}秒間 に"
echo "WASD / ←→ キーで操作してください。"
echo ""
echo "3秒後に開始します..."
sleep 3

# cub3D 起動
cd "$CUB3D_DIR"
./cub3D "$MAP" &
CUB3D_PID=$!
sleep 3

# ウィンドウ位置取得
BOUNDS=$(/Library/Frameworks/Python.framework/Versions/3.10/bin/python3 -c "
from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID
wins = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
for w in wins:
    if 'cub3D' in w.get('kCGWindowOwnerName', ''):
        b = w.get('kCGWindowBounds', {})
        print(f\"{int(b['X'])} {int(b['Y'])+28} {int(b['Width'])} {int(b['Height'])-28}\")
        break
")
read X Y W H <<< "$BOUNDS"
echo "📐 録画領域: ${X},${Y} ${W}x${H}"
echo ""
echo "🔴 録画開始 (${DURATION}秒) - 今すぐ cub3D ウィンドウをクリックしてキー操作!"

# screencapture で録画
MOV=/tmp/cub3d_gameplay.mov
rm -f "$MOV"
screencapture -v -V"$DURATION" -R"$X,$Y,$W,$H" -x "$MOV"

echo "✅ 録画完了"

# cub3D 停止
kill $CUB3D_PID 2>/dev/null
wait $CUB3D_PID 2>/dev/null

# GIF 変換
echo "🎞️  GIF に変換中..."
GIF="$OUT_DIR/gameplay.gif"
PALETTE=/tmp/palette.png
ffmpeg -y -i "$MOV" -vf "fps=12,scale=640:-1:flags=lanczos,palettegen" "$PALETTE" > /dev/null 2>&1
ffmpeg -y -i "$MOV" -i "$PALETTE" -lavfi "fps=12,scale=640:-1:flags=lanczos [x]; [x][1:v] paletteuse" "$GIF" > /dev/null 2>&1
rm "$PALETTE"

SIZE=$(du -h "$GIF" | cut -f1)
echo "✅ 保存完了: $GIF ($SIZE)"
