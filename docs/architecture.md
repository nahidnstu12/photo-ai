# Architecture

## System context

**photo-ai** is a batch-oriented image processing system. Clients (CLI, REST API, future integrations) submit product photos; the orchestrator runs a fixed multi-stage pipeline and writes artifacts to disk.

No database in MVP — filesystem is the source of truth for job state (Phase 6 adds Redis for queue metadata only).

---

## Services

### orchestrator (Python / FastAPI)

- **Port:** 8090
- **Implemented:**
  - `GET /health` — `phase` reflects orchestrator milestone (currently `3`)
  - `POST /api/v1/stages/rembg` — single-stage test upload
  - CLI: `python -m app.cli stage rembg|upscale`
  - Pipeline modules: `remove_bg`, `composite`, `upscale`
- **Phase 5:** `runner.py`, `polish.py`, `POST /api/v1/enhance`, `cli run`
- **Phase 6 (not yet):** `/api/v1/jobs/{id}`
- **Contains:** rembg, Real-ESRGAN (torch CPU in Docker)
- **Does not contain:** SD checkpoint weights

### comfyui

- **Port:** 8188
- **Implemented:**
  - Image from `services/comfyui/` (ComfyUI **v0.3.49**, CPU default `--cpu` on Mac)
  - Checkpoints: `data/models/comfyui/checkpoints/`
  - I/O: `data/models/comfyui/input/`, `output/`
  - Workflow: `workflows/polish_catalog.json` (manual `/prompt` via `scripts/comfyui-prompt-test.sh`)
- **Phase 5:** orchestrator HTTP client calls this service

### redis (Phase 6+)

- Job queue backing store
- Ephemeral job status (TTL configurable)

---

## Pipeline data flow

```
┌──────────┐    ┌─────────────┐    ┌────────────┐    ┌─────────────┐    ┌────────────┐    ┌────────┐
│  input   │───►│ rembg       │───►│ composite  │───►│ Real-ESRGAN │───►│ ComfyUI     │───►│ output │
│  JPG/PNG │    │ stage1_nobg │    │ (in-mem)   │    │ stage2_up   │    │ stage3_sd   │    │  JPG   │
└──────────┘    └─────────────┘    └────────────┘    └─────────────┘    └─────────────┘    └────────┘
                      │                                      │                  │
                      └──────── transparent PNG ─────────────┘                  │
                                                                                  │
                                         skip if pipeline_mode=deterministic ────┘
```

### Stage details

| Stage | Input | Output | Deterministic? |
|-------|-------|--------|----------------|
| rembg | Raw photo | RGBA PNG (subject) | Yes |
| composite | RGBA PNG | RGB PNG on white/grey | Yes |
| Real-ESRGAN | RGB PNG | RGB PNG 2x | Yes |
| SD img2img | RGB PNG | RGB PNG polished | No (seed controls variance) |

---

## Docker topology

```yaml
# As in docker-compose.yml (simplified)
services:
  orchestrator:
    volumes: [./data:/data, ./workflows:/workflows:ro]
    # depends_on comfyui — add in phase 5 when polish is wired

  comfyui:
    volumes:
      - ./data/models/comfyui/checkpoints:/opt/ComfyUI/models/checkpoints
      - ./data/models/comfyui/input:/opt/ComfyUI/input
      - ./data/models/comfyui/output:/opt/ComfyUI/output
      - ./workflows:/workflows:ro
    environment:
      COMFYUI_EXTRA_ARGS: --cpu   # Mac Docker; GPU: docker-compose.gpu.yml
```

### Volume strategy

| Host path | Contents | Size (approx) |
|-----------|----------|---------------|
| `data/models/comfyui/checkpoints/` | `realisticVision_v51.safetensors` | ~2–4 GB |
| `data/models/realesrgan/` | `RealESRGAN_x4plus.pth` | ~64 MB |
| `data/models/rembg/` | U2-Net weights (auto-download) | ~170 MB each |
| `data/input`, `stage*`, `output` | Pipeline I/O | grows with batch |

---

## Configuration

All config via environment (see `.env.example`):

| Variable | Purpose |
|----------|---------|
| `COMFYUI_URL` | `http://comfyui:8188` inside compose |
| `WORKFLOW_POLISH_PATH` | `/workflows/polish_catalog.json` |
| `PIPELINE_DENOISE` | Default 0.30 |
| `PIPELINE_UPSCALE` | Default 2 |
| `REMBG_MODEL` | Default `u2net_cloth_seg` |
| `DATA_DIR` | `/data` |
| `PIPELINE_MODE` | `full` or `deterministic` |

---

## Deployment modes

### Mode A — Full Docker (Linux server, NVIDIA)

Use `docker-compose.yml` + `docker-compose.gpu.yml`. ComfyUI gets GPU. Best for production batch.

### Mode B — Hybrid Mac dev (recommended for M4)

- ComfyUI runs **natively** on host (MPS): `python main.py --force-fp16`
- Orchestrator + rembg + ESRGAN in Docker, or all native
- Set `COMFYUI_URL=http://host.docker.internal:8188`

Document in Phase 1 README which mode you're using.

### Mode C — CPU-only Docker

All services in Docker, no GPU. SD stage is slow but works for CI/smoke tests with tiny images.

---

## API sketch (Phase 5)

```
POST /api/v1/enhance
  Content-Type: multipart/form-data
  file: image
  options: { pipeline_mode, denoise, aesthetic_preset }

Response 200 (sync MVP):
  { "job_id": "...", "output_path": "/data/output/foo.jpg", "stages": [...] }
```

---

## Failure handling

- Stage failure → stop pipeline, preserve intermediate artifacts, return error with `failed_stage`
- ComfyUI timeout → configurable (default 120s per image)
- OOM on ComfyUI → reduce batch to 1; document `--force-fp16` and taesd VAE
- rembg partial cut → retry with `u2net_cloth_seg`; flag for manual review in Phase 7

---

## Security (MVP)

- Local/trusted network only — no auth on API
- Do not expose ComfyUI port publicly (no built-in auth)
- Phase 7+: optional API key header for orchestrator
