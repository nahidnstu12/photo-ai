#!/usr/bin/env bash
# Download ML model weights into data/models/ (not committed to git)
# Run from repo root: ./scripts/download-models.sh

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MODELS_DIR="${MODELS_DIR:-$ROOT/data/models}"

mkdir -p "$MODELS_DIR/realesrgan" "$MODELS_DIR/comfyui/checkpoints"

echo "==> Real-ESRGAN x4plus"
REALESRGAN_URL="https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus.pth"
REALESRGAN_DEST="$MODELS_DIR/realesrgan/RealESRGAN_x4plus.pth"
if [[ ! -f "$REALESRGAN_DEST" ]]; then
  curl -L "$REALESRGAN_URL" -o "$REALESRGAN_DEST"
  echo "    saved: $REALESRGAN_DEST"
else
  echo "    exists: $REALESRGAN_DEST"
fi

echo ""
echo "==> Stable Diffusion checkpoint (manual)"
echo "    Download realisticVision v5.1 (.safetensors) from HuggingFace or CivitAI"
echo "    Place at: $MODELS_DIR/comfyui/checkpoints/realisticVision_v51.safetensors"
echo "    Or mount volume comfyui_models in Docker (see docs/phases/04-comfyui-service.md)"

echo ""
echo "==> rembg models"
echo "    Auto-download on first rembg run (~170MB). Optional cache: data/models/rembg/"

echo ""
echo "Done. See docs/phases/ for next steps."
