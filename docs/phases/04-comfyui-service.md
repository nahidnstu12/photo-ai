# Phase 4 — ComfyUI Service

**Status:** complete  
**Depends on:** [Phase 1](./01-docker-foundation.md)  
**Parallel with:** Phases 2–3

---

## Goal

ComfyUI runs in Docker (or documented native/hybrid setup), loads checkpoint, executes exported img2img workflow via HTTP API.

---

## Scope IN

- `services/comfyui/Dockerfile` + entrypoint (`--listen 0.0.0.0`; GPU: `--force-fp16` via override)
- Add `comfyui` service to `docker-compose.yml` with healthcheck (`GET /system_stats` or `/`)
- `workflows/polish_catalog.json` — minimal img2img API workflow (placeholder OK initially)
- Document checkpoint download → `data/models/comfyui/checkpoints/realisticVision_v51.safetensors`
- Manual verification: submit test workflow via curl to `/prompt`
- `docker-compose.gpu.yml` stub for NVIDIA (commented example)

## Scope OUT

- Orchestrator ComfyUI client (Phase 5)
- Dynamic prompt injection (hardcode in workflow JSON first)
- ComfyUI Manager UI setup in container (optional dev only)

---

## Workflow JSON (minimum nodes)

1. Load Checkpoint → realisticVision v5.1
2. Load Image
3. CLIP Text Encode (positive + negative)
4. KSampler — steps 20, CFG 7, DPM++ 2M Karras, **denoise 0.3**
5. VAE Decode
6. Save Image

Export via ComfyUI: **Workflow → Export (API)** — save to `workflows/polish_catalog.json`.

### Default prompts (embed in workflow or Phase 5 inject)

See [glossary.md](../glossary.md).

---

### As implemented

| Piece | Detail |
|-------|--------|
| Image | ComfyUI **v0.3.49** (`ARG COMFYUI_REF` in Dockerfile) |
| CPU default | `COMFYUI_EXTRA_ARGS=--cpu` (Mac Docker) |
| GPU Linux | `docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d` |
| Workflow | `workflows/polish_catalog.json` (nodes 1–8, denoise 0.3) |
| Test script | `scripts/comfyui-prompt-test.sh` |

---

## Verification

```bash
# After checkpoint download (see README)
docker compose build comfyui && docker compose up -d comfyui
docker compose ps                    # comfyui healthy
curl -sf http://localhost:8188/system_stats | jq .

cp data/stage2_upscale/sample.png data/models/comfyui/input/input.png
./scripts/comfyui-prompt-test.sh
ls data/models/comfyui/output/
```

For hybrid Mac: run ComfyUI natively on :8188; set `COMFYUI_URL=http://host.docker.internal:8188` in orchestrator `.env` (phase 5).

---

## Done when

- [x] ComfyUI container starts and stays healthy
- [x] Checkpoint loads without OOM (document RAM/GPU requirements)
- [x] `workflows/polish_catalog.json` committed (API format)
- [x] One manual `/prompt` run produces image in ComfyUI output dir
- [x] Model download steps in README + `scripts/download-models.sh`
- [x] GPU override file documented

---

## Agent notes

- Checkpoint files are **never committed** — .gitignore + download script only.
- ComfyUI image pins a known-good tag/commit when possible.
- If Docker GPU fails on Mac, document hybrid mode — don't block phase on GPU in container.
