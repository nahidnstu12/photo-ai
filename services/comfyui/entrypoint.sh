#!/bin/sh
set -e
cd /opt/ComfyUI
# Mac Docker / CPU: --cpu  |  Linux NVIDIA: set COMFYUI_EXTRA_ARGS=--force-fp16
exec python main.py --listen 0.0.0.0 --port 8188 ${COMFYUI_EXTRA_ARGS:---cpu}
