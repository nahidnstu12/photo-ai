# photo-ai

Local **Docker-based** product photo enhancement pipeline — raw clothing photo → catalog-ready image.

**No cloud APIs.** Stack: Python · rembg · Real-ESRGAN · ComfyUI (SD img2img).

---

## Status

**Phase 4 complete** — rembg, Real-ESRGAN 2x upscale, ComfyUI service. Next: full pipeline API (Phase 5).

| Doc | Description |
|-----|-------------|
| [docs/learning/README.md](docs/learning/README.md) | **Start here if new to the stack** |
| [docs/00-plan.md](docs/00-plan.md) | Master plan & phase index |
| [docs/00-overview.md](docs/00-overview.md) | Project overview |
| [docs/architecture.md](docs/architecture.md) | System design |
| [docs/agent-guidelines.md](docs/agent-guidelines.md) | AI agent instructions |
| [docs/phases/](docs/phases/) | Phase-by-phase implementation |

Original concepts: `photo_enhancement_guide.docx`

---

## Pipeline

```
input → rembg → white composite → Real-ESRGAN 2x → SD polish (optional) → output JPG
```

**Catalog-safe defaults:** denoise `0.30`, upscale `2x`, rembg model `u2net_cloth_seg`.

---

## Prerequisites

- Docker Desktop (Compose v2)
- ~25 GB disk (models + cache)
- 16 GB RAM minimum
- **Mac M4:** Docker has no GPU — use [hybrid dev mode](docs/architecture.md#mode-b--hybrid-mac-dev-recommended-for-m4) for ComfyUI (native MPS) after Phase 4

---

## Quick start (Phase 1+)

```bash
cp .env.example .env
docker compose build orchestrator
docker compose up -d
curl -sf http://localhost:8090/health | jq .
# → {"status":"ok","phase":1,"data_dir":"/data","data_dirs_ready":true}
```

On startup the orchestrator ensures `data/input`, `output`, `stage1_nobg`, `stage2_upscale`, `stage3_sd`, and `models` exist under the bind-mounted `./data`.

**Mac M4:** Docker has no MPS. Use [hybrid dev](docs/architecture.md#mode-b--hybrid-mac-dev-recommended-for-m4) after Phase 4 — native ComfyUI on host, orchestrator in Docker with `COMFYUI_URL=http://host.docker.internal:8188`.

### Phase 2 — rembg stage

```bash
# Put a clothing photo in data/input/, then:
docker compose exec orchestrator python -m app.cli stage rembg \
  --input /data/input/your.jpg \
  --output /data/stage1_nobg/your.png

# Or HTTP (multipart upload):
curl -sf -F "file=@data/input/your.jpg" http://localhost:8090/api/v1/stages/rembg | jq .
```

Models cache under `data/models/rembg/` on first run (`REMBG_MODEL`, default `u2net_cloth_seg`).

### Model downloads (you run these)

```bash
cd photo-ai
mkdir -p data/models/realesrgan data/models/comfyui/{checkpoints,input,output}

# Real-ESRGAN ~64MB (Phase 3)
curl -fL -o data/models/realesrgan/RealESRGAN_x4plus.pth \
  https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth

# ComfyUI checkpoint ~2GB (Phase 4) — filename must match workflow JSON
curl -fL -o data/models/comfyui/checkpoints/realisticVision_v51.safetensors \
  'https://huggingface.co/SG161222/Realistic_Vision_V5.1_noVAE/resolve/main/realisticVisionV51_v51VAE.safetensors'
```

`./scripts/download-models.sh` only prints the same commands (no network).

### Phase 3 — upscale

```bash
docker compose build orchestrator && docker compose up -d
docker compose exec orchestrator python -m app.cli stage upscale \
  --input /data/stage1_nobg/sample.png \
  --output /data/stage2_upscale/sample.png
```

### Phase 4 — ComfyUI

```bash
docker compose build comfyui && docker compose up -d comfyui
curl -sf http://localhost:8188/system_stats | head
# Test prompt (copy image to data/models/comfyui/input/input.png first):
./scripts/comfyui-prompt-test.sh
```

**Linux + NVIDIA:** `docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d`

Full pipeline available after **Phase 5**.

---

## Project layout

```
photo-ai/
├── .cursor/rules/          # Cursor agent rules
├── docs/                   # Plans & architecture
├── services/
│   ├── orchestrator/       # FastAPI + pipeline (Phase 1+)
│   └── comfyui/            # ComfyUI image (Phase 4+)
├── workflows/              # ComfyUI API JSON
├── scripts/                # Model download helpers
└── data/                   # I/O + models (gitignored)
```

---

## For AI agents

1. Read `docs/00-plan.md`
2. Find lowest incomplete phase in `docs/phases/`
3. Follow `docs/agent-guidelines.md`
4. Obey `.cursor/rules/core.mdc`

---

## License

Private / internal — adjust as needed.
