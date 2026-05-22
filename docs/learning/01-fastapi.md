# FastAPI — orchestrator crash course

**In photo-ai:** FastAPI is the HTTP server that receives images and runs pipeline stages. It does **not** run AI models itself (except calling rembg/ESRGAN as Python libs).

---

## What is FastAPI?

A Python web framework for building APIs — like Laravel routes or Express, but with automatic OpenAPI docs.

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}
```

Run → `http://localhost:8090/health` returns JSON.

**Why we use it:** async-friendly, pydantic validation, easy file uploads, good for ML microservices.

---

## How photo-ai uses it

| Endpoint | Phase | Purpose |
|----------|-------|---------|
| `GET /health` | 1 | Docker healthcheck, "is server up?" |
| `POST /api/v1/enhance` | 5 | Upload image → full pipeline → output path |
| `POST /api/v1/jobs` | 6 | Batch async processing |

---

## File upload example (what Phase 5 looks like)

```python
from fastapi import FastAPI, UploadFile, File, Form

app = FastAPI()

@app.post("/api/v1/enhance")
async def enhance(
    file: UploadFile = File(...),
    pipeline_mode: str = Form("full"),
    denoise: float = Form(0.30),
):
    # 1. Save upload to /data/input/tmp_xyz.jpg
    input_path = save_upload(file)

    # 2. Run pipeline (your code, not FastAPI magic)
    result = run_pipeline(
        input_path,
        mode=pipeline_mode,
        denoise=denoise,
    )

    # 3. Return JSON
    return {
        "status": "completed",
        "output_path": str(result.output_path),
        "artifacts": result.artifacts,
    }
```

**You test with curl:**

```bash
curl -X POST http://localhost:8090/api/v1/enhance \
  -F "file=@data/input/shirt.jpg" \
  -F "pipeline_mode=deterministic"
```

---

## Config via environment

FastAPI app reads settings at startup (pydantic-settings):

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    data_dir: str = "/data"
    comfyui_url: str = "http://comfyui:8188"
    pipeline_denoise: float = 0.30
    rembg_model: str = "u2net_cloth_seg"

    class Config:
        env_file = ".env"
```

`.env.example` in repo → Docker injects vars → Python reads them.

---

## Project structure (orchestrator)

```
services/orchestrator/
├── app/
│   ├── main.py          ← FastAPI app, routes
│   ├── config.py        ← Settings from env
│   ├── cli.py           ← same pipeline, terminal entry
│   └── pipeline/
│       ├── runner.py    ← runs stages in order
│       ├── remove_bg.py
│       ├── upscale.py
│       └── polish.py    ← HTTP client to ComfyUI
└── Dockerfile
```

**Key idea:** Routes are thin. Business logic lives in `pipeline/`.

---

## CLI vs API — same brain

```bash
# API (remote trigger)
curl -F "file=@shirt.jpg" http://localhost:8090/api/v1/enhance

# CLI (same pipeline code, no HTTP)
docker compose exec orchestrator python -m app.cli run --input /data/input/shirt.jpg
```

Both call `pipeline.runner.run()`. Don't duplicate logic in route handlers.

---

## Docker + healthcheck

```yaml
# docker-compose.yml (simplified)
orchestrator:
  ports: ["8090:8090"]
  healthcheck:
    test: ["CMD", "curl", "-sf", "http://localhost:8090/health"]
```

Docker marks container **healthy** only when `/health` returns 200. ComfyUI service waits for this pattern too.

---

## Error handling (catalog project style)

```python
# Don't return 500 with empty body — tell which stage failed
raise HTTPException(
    status_code=422,
    detail={
        "message": "Pipeline failed at upscale",
        "failed_stage": "realesrgan",
        "artifacts": {"stage1_nobg": "/data/stage1_nobg/shirt.png"},
    },
)
```

Intermediate files stay on disk so you can inspect them.

---

## FastAPI auto docs (bonus)

When server runs, visit:

- `http://localhost:8090/docs` — Swagger UI
- `http://localhost:8090/redoc` — alternative docs

Useful for testing uploads without writing curl every time.

---

## What to remember

1. FastAPI = **HTTP shell** around pipeline
2. Upload → save file → `run_pipeline()` → JSON response
3. Config from `.env`, not hardcoded
4. CLI reuses same pipeline module

---

## Next

[02-rembg.md](./02-rembg.md) — first stage that actually changes the image.
