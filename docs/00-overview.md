# photo-ai — Overview

**Local, Docker-based product photo enhancement** for e-commerce catalog images (clothing-first).

Raw photo → background removal → studio composite → upscale → optional SD polish → catalog-ready JPG.

## Why this project exists

Merchants upload inconsistent product photos (messy backgrounds, low resolution, uneven lighting). Cloud APIs (Photoroom, etc.) cost per image and send data off-device. This pipeline runs **entirely local** with reproducible stages and tunable quality levers.

## What it is NOT

- Not a general photo editor UI (batch/API first)
- Not for **custom print** workflows where the original pixel must be preserved (e.g. mug photos with user artwork)
- Not cloud-hosted inference (MVP)

## Documentation map

| Doc | Purpose |
|-----|---------|
| [00-plan.md](./00-plan.md) | Master plan, locked decisions, phase index |
| [architecture.md](./architecture.md) | System design, data flow, Docker topology |
| [agent-guidelines.md](./agent-guidelines.md) | How AI agents should work in this repo |
| [glossary.md](./glossary.md) | Terms and quality levers |
| [phases/](./phases/) | One file per implementation phase |

## Original reference

`../photo_enhancement_guide.docx` — conceptual source (Mac-native setup). **Docker layout in `docs/` supersedes** the docx for deployment and repo structure.

## Quick start (after Phase 1)

```bash
cp .env.example .env
docker compose up -d
curl http://localhost:8090/health
```

Full pipeline available after Phase 5.

## Hardware expectations

| Environment | GPU | ~Time/image (full pipeline) |
|-------------|-----|----------------------------|
| Mac M4 16GB (hybrid dev) | MPS native ComfyUI | ~60s |
| Mac Docker (CPU) | None | 3–10 min (SD slow) |
| Linux + NVIDIA 8GB+ | CUDA | ~30–60s |

Build incrementally: **rembg → ESRGAN → SD last**.
