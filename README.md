# photo-ai

Local **Docker-based** product photo enhancement pipeline — raw clothing photo → catalog-ready image.

**No cloud APIs.** Stack: Python · rembg · Real-ESRGAN · ComfyUI (SD img2img).

---

## Status

| Phase | What | State |
|-------|------|--------|
| 1 | Docker + `/health` | ✅ |
| 2 | rembg + white composite | ✅ CLI + `POST /api/v1/stages/rembg` |
| 3 | Real-ESRGAN 2× | ✅ CLI |
| 4 | ComfyUI service | ✅ manual workflow test |
| 5 | Full pipeline `run` / `enhance` | ✅ |
| 6–7 | Batch queue, ops | ❌ **next** |

Details: [docs/00-plan.md](docs/00-plan.md)

---

## Pipeline

```
input → rembg → white composite → Real-ESRGAN 2x → SD polish (optional) → output JPG
         └─ stage1_nobg/          └─ stage2_upscale/    └─ stage3_sd/ → output/
```

**Catalog-safe defaults:** denoise `0.30`, upscale `2x`, rembg `u2net_cloth_seg` (use `u2net` if cutout fails).

---

## Prerequisites

- Docker Desktop (Compose v2)
- ~25 GB disk (models + cache)
- 16 GB RAM minimum (upscale on large images is heavy in Docker)
- **Mac M4:** Docker has no GPU — [hybrid dev](docs/architecture.md#mode-b--hybrid-mac-dev-recommended-for-m4) for ComfyUI

---

## Quick start

```bash
cp .env.example .env
docker compose build
docker compose up -d
curl -sf http://localhost:8090/health | jq .
```

### Model downloads (you run these)

```bash
mkdir -p data/models/realesrgan data/models/comfyui/{checkpoints,input,output}

# Real-ESRGAN ~64MB — URL must be v0.1.0 (not v0.2.2.4)
curl -fL -o data/models/realesrgan/RealESRGAN_x4plus.pth \
  https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth
ls -lh data/models/realesrgan/RealESRGAN_x4plus.pth   # ~64M

# ComfyUI checkpoint ~2GB
curl -fL -o data/models/comfyui/checkpoints/realisticVision_v51.safetensors \
  'https://huggingface.co/SG161222/Realistic_Vision_V5.1_noVAE/resolve/main/realisticVisionV51_v51VAE.safetensors'
```

`./scripts/download-models.sh` prints the same commands (no network).

### Manual pipeline (phases 2–3)

```bash
cp your-photo.jpg data/input/product.jpg

docker compose exec orchestrator python -m app.cli stage rembg \
  --input /data/input/product.jpg \
  --output /data/stage1_nobg/product.png
# Bad cutout? Add: --model u2net

docker compose exec orchestrator python -m app.cli stage upscale \
  --input /data/stage1_nobg/product.png \
  --output /data/stage2_upscale/product.png
```

### ComfyUI (phase 4, optional)

```bash
docker compose up -d comfyui
curl -sf http://localhost:8188/system_stats | jq .
cp data/stage2_upscale/product.png data/models/comfyui/input/input.png
./scripts/comfyui-prompt-test.sh
```

**Linux + NVIDIA:** `docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d`

### Full pipeline (phase 5)

```bash
docker compose build orchestrator && docker compose up -d

# No ComfyUI needed
docker compose exec orchestrator python -m app.cli run \
  --input /data/input/product.jpg --mode deterministic

# With SD polish (comfyui up + checkpoint downloaded)
docker compose exec orchestrator python -m app.cli run \
  --input /data/input/product.jpg --mode full --denoise 0.30

ls -la data/output/

curl -X POST http://localhost:8090/api/v1/enhance \
  -F "file=@data/input/product.jpg" \
  -F "pipeline_mode=deterministic"
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| rembg tall strip / broken mask | `REMBG_MODEL=u2net` or `--model u2net` |
| upscale pickle error | Re-download `.pth` (~64MB, not 9-byte "Not Found") |
| upscale OOM (exit 137) | More Docker RAM; expect minutes on CPU |
| `invalid choice: upscale` | `docker compose build orchestrator && docker compose up -d` |
| ComfyUI build fails on frontend pkg | Use current Dockerfile (ComfyUI v0.3.49) |

---

## Project layout

```
photo-ai/
├── services/orchestrator/app/   # FastAPI + pipeline + CLI
├── services/comfyui/            # ComfyUI v0.3.49 image
├── workflows/polish_catalog.json
├── scripts/
└── data/                        # I/O + models (gitignored)
```

---

## Docs

| Doc | Description |
|-----|-------------|
| [docs/00-plan.md](docs/00-plan.md) | Master plan + implementation table |
| [docs/phases/](docs/phases/) | Per-phase scope & verification |
| [docs/architecture.md](docs/architecture.md) | Docker topology (aligned to compose) |

---

## For AI agents

Start at [docs/00-plan.md](docs/00-plan.md) → implement **phase 05** next.
