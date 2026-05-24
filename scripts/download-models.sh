#!/usr/bin/env bash
# Print model download commands (does not download anything).
# Run from repo root: ./scripts/download-models.sh

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MODELS_DIR="${MODELS_DIR:-$ROOT/data/models}"

mkdir -p \
  "$MODELS_DIR/realesrgan" \
  "$MODELS_DIR/comfyui/checkpoints" \
  "$MODELS_DIR/comfyui/input" \
  "$MODELS_DIR/comfyui/output"

cat <<EOF
# photo-ai — model downloads (run these yourself from repo root)

mkdir -p data/models/realesrgan data/models/comfyui/{checkpoints,input,output}

# --- Real-ESRGAN (~64MB, Phase 3) ---
curl -fL -o data/models/realesrgan/RealESRGAN_x4plus.pth \\
  https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth

# verify (~67MB):
# ls -lh data/models/realesrgan/RealESRGAN_x4plus.pth

# --- ComfyUI checkpoint (~2GB, Phase 4) ---
# Rename on disk must match workflows/polish_catalog.json: realisticVision_v51.safetensors
curl -fL -o data/models/comfyui/checkpoints/realisticVision_v51.safetensors \\
  'https://huggingface.co/SG161222/Realistic_Vision_V5.1_noVAE/resolve/main/realisticVisionV51_v51VAE.safetensors'

# Or download from CivitAI manually and place at:
#   $MODELS_DIR/comfyui/checkpoints/realisticVision_v51.safetensors

# --- rembg (Phase 2) ---
# No manual download — first rembg run auto-fetches ~170MB to data/models/rembg/

EOF
