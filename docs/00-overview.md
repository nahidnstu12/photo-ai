# photo-ai — Overview

**Local, Docker-based product photo enhancement** for e-commerce catalog images (clothing-first).

Raw photo → background removal → studio composite → upscale → optional SD polish → catalog-ready JPG.

## Current progress

| Stage | Status |
|-------|--------|
| Docker + health | ✅ |
| rembg + white composite | ✅ CLI + test API |
| Real-ESRGAN 2× | ✅ CLI |
| ComfyUI service | ✅ container + manual workflow test |
| Full pipeline (`run` / `enhance`) | ✅ Phase 5 |

See [00-plan.md](./00-plan.md) for the full phase table.

## Why this project exists

Merchants upload inconsistent product photos (messy backgrounds, low resolution, uneven lighting). Cloud APIs (Photoroom, etc.) cost per image and send data off-device. This pipeline runs **entirely local** with reproducible stages and tunable quality levers.

## What it is NOT

- Not a general photo editor UI (batch/API first)
- Not for **custom print** workflows where the original pixel must be preserved (e.g. mug photos with user artwork)
- Not cloud-hosted inference (MVP)

## Documentation map

| Doc | Purpose |
|-----|---------|
| [00-plan.md](./00-plan.md) | Master plan, implementation status, phase index |
| [architecture.md](./architecture.md) | System design, data flow, Docker topology |
| [agent-guidelines.md](./agent-guidelines.md) | How AI agents should work in this repo |
| [glossary.md](./glossary.md) | Terms and quality levers |
| [learning/](./learning/) | **Crash course** — FastAPI, rembg, ESRGAN, ComfyUI |
| [phases/](./phases/) | One file per implementation phase |

## Quick start (manual pipeline, phases 1–4)

```bash
cp .env.example .env
docker compose build
docker compose up -d

# 1) Input
cp your-photo.jpg data/input/product.jpg

# 2) rembg (+ white composite)
docker compose exec orchestrator python -m app.cli stage rembg \
  --input /data/input/product.jpg \
  --output /data/stage1_nobg/product.png
# If cutout is broken, retry: --model u2net

# 3) upscale (download Real-ESRGAN weights first — see README)
docker compose exec orchestrator python -m app.cli stage upscale \
  --input /data/stage1_nobg/product.png \
  --output /data/stage2_upscale/product.png

# 4) optional SD polish — manual ComfyUI for now
# cp data/stage2_upscale/product.png data/models/comfyui/input/input.png
# ./scripts/comfyui-prompt-test.sh
```

Full one-shot API/CLI: `POST /api/v1/enhance` or `python -m app.cli run --input /data/input/foo.jpg`.

## Hardware expectations

| Environment | GPU | ~Time/image (full pipeline) |
|-------------|-----|----------------------------|
| Mac M4 16GB (hybrid dev) | MPS native ComfyUI | ~60s |
| Mac Docker (CPU) | None | rembg ~20s; upscale minutes on large images |
| Linux + NVIDIA 8GB+ | CUDA | ~30–60s |

Build incrementally: **rembg → ESRGAN → SD last**.
