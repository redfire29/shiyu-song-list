#!/usr/bin/env bash
set -e

# 切換至專案根目錄
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

export PATH="/usr/local/bin:/opt/homebrew/bin:$PATH"

echo "=================================================="
echo "      YouTube 歌回時間戳轉錄系統 - 環境安裝        "
echo "=================================================="

# 1. 尋找相容且穩定的 Python 版本 (優先選用 Apple/Xcode 內建的 Python 3.9 ~ 3.12，避開 3.14 函式庫衝突)
PYTHON_CANDIDATES=(
    "/usr/bin/python3"
    "$(which python3.11 2>/dev/null || true)"
    "$(which python3.10 2>/dev/null || true)"
    "$(which python3.9 2>/dev/null || true)"
    "$(which python3 2>/dev/null || true)"
)

TARGET_PYTHON=""
for py in "${PYTHON_CANDIDATES[@]}"; do
    if [ -n "$py" ] && [ -x "$py" ]; then
        VER=$("$py" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || true)
        MAJOR=$(echo "$VER" | cut -d. -f1)
        MINOR=$(echo "$VER" | cut -d. -f2)
        if [ "$MAJOR" -eq 3 ] && [ "$MINOR" -ge 9 ] && [ "$MINOR" -le 12 ]; then
            TARGET_PYTHON="$py"
            echo "-> 找到相容的 Python: $TARGET_PYTHON (版本: $VER)"
            break
        fi
    fi
done

if [ -z "$TARGET_PYTHON" ]; then
    echo "⚠️ 未找到 3.9 ~ 3.12 的 Python，嘗試使用預設 python3..."
    TARGET_PYTHON="$(which python3)"
fi

# 2. 建立虛擬環境 .venv
if [ ! -d ".venv" ]; then
    echo "-> 建立獨立虛擬環境 (.venv)..."
    "$TARGET_PYTHON" -m venv .venv
else
    echo "-> 虛擬環境 (.venv) 已存在，繼續更新依賴..."
fi

# 3. 啟用虛擬環境並安裝相依套件
source .venv/bin/activate
echo "-> 升級 pip..."
python -m pip install --upgrade pip

echo "-> 安裝 Whisper 與相關套件 (從 requirements-whisper.txt)..."
python -m pip install -r requirements-whisper.txt

# 4. 檢測 Apple Silicon MPS 加速與 ffmpeg
echo ""
echo "=================================================="
echo "               環境驗證與硬體檢測                 "
echo "=================================================="
python -c "import torch; print(f'✓ PyTorch 版本: {torch.__version__}'); print(f'✓ Apple Silicon (MPS) GPU 加速: {torch.backends.mps.is_available()}')"

if command -v ffmpeg >/dev/null 2>&1; then
    echo "✓ ffmpeg 狀態: 已安裝 ($(which ffmpeg))"
else
    echo "⚠️ 警告: 未在 PATH 中找到 ffmpeg，請確保已安裝 ffmpeg (例如 brew install ffmpeg)"
fi

echo ""
echo "🎉 環境設定完成！"
echo "使用方式："
echo "  1. 啟用環境: source .venv/bin/activate"
echo "  2. 執行轉錄: python yt_whisper_transcriber.py <YouTube網址>"
echo "=================================================="
