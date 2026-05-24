#!/usr/bin/env bash
# Submit polish_catalog workflow to ComfyUI (manual Phase 4 check).
# Usage:
#   cp your.png data/models/comfyui/input/input.png   # ComfyUI LoadImage path
#   ./scripts/comfyui-prompt-test.sh

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMFYUI_URL="${COMFYUI_URL:-http://localhost:8188}"
WORKFLOW="$ROOT/workflows/polish_catalog.json"
INPUT_DIR="$ROOT/data/models/comfyui/input"

mkdir -p "$INPUT_DIR"
if [[ ! -f "$INPUT_DIR/input.png" ]]; then
  echo "Place test image at: $INPUT_DIR/input.png"
  exit 1
fi

PROMPT=$(cat "$WORKFLOW")
curl -sf -X POST "$COMFYUI_URL/prompt" \
  -H "Content-Type: application/json" \
  -d "{\"prompt\":$PROMPT}"

echo ""
echo "Check ComfyUI output under data/models/comfyui/output/ (or container /opt/ComfyUI/output)"
