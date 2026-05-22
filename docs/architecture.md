# Architecture

## System context

**photo-ai** is a batch-oriented image processing system. Clients (CLI, REST API, future integrations) submit product photos; the orchestrator runs a fixed multi-stage pipeline and writes artifacts to disk.

No database in MVP — filesystem is the source of truth for job state (Phase 6 adds Redis for queue metadata only).

---

## Services

### orchestrator (Python / FastAPI)

- **Port:** 8090
- **Responsibilities:**
  - HTTP API (`/health`, `/api/v1/enhance`, `/api/v1/jobs/{id}` in Phase 6)
  - Pipeline orchestration — calls stages in order
  - ComfyUI HTTP client (submit workflow, poll, fetch result)
  - CLI: `python -m app.cli run --input data/input/`
- **Contains:** rembg, Real-ESRGAN inference code (Python/subprocess)
- **Does not contain:** SD model weights

### comfyui

- **Port:** 8188
- **Responsibilities:**
  - Run ComfyUI server headlessly
  - Load checkpoint from mounted volume
  - Execute img2img workflows submitted via `/prompt`
- **Image:** Based on official/community ComfyUI Docker pattern; custom entrypoint for `--listen 0.0.0.0 --force-fp16`

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
# Logical compose network
services:
  orchestrator:
    depends_on:
      comfyui: { condition: service_healthy }  # when SD enabled
    volumes:
      - ./data:/data
      - ./workflows:/workflows:ro

  comfyui:
    volumes:
      - comfyui_models:/comfyui/models
      - ./workflows:/workflows:ro

volumes:
  comfyui_models:
  rembg_models:      # optional cache
  realesrgan_weights:
```

### Volume strategy

| Mount | Contents | Size (approx) |
|-------|----------|---------------|
| `comfyui_models` | `checkpoints/realisticVision_v51.safetensors` | ~2–4 GB |
| `realesrgan_weights` | `RealESRGAN_x4plus.pth` | ~64 MB |
| `rembg_models` | U2-Net / cloth seg (auto-download) | ~170 MB |
| `./data` | I/O and stage artifacts | grows with batch |

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
