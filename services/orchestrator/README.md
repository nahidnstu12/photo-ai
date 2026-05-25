# Orchestrator service

FastAPI + per-stage CLI + full pipeline (phases 1–5).

## API

| Endpoint | Status |
|----------|--------|
| `GET /health` | ✅ |
| `POST /api/v1/stages/rembg` | ✅ |
| `POST /api/v1/enhance` | ✅ |

`POST /api/v1/enhance` — multipart `file`, optional `pipeline_mode` (`full`|`deterministic`), `denoise`, `seed`.

## CLI

```bash
python -m app.cli run --input /data/input/x.jpg --mode deterministic
python -m app.cli run --input /data/input/x.jpg --mode full --denoise 0.30

python -m app.cli stage rembg --input /data/input/x.jpg --output /data/stage1_nobg/x.png
python -m app.cli stage upscale --input /data/stage1_nobg/x.png --output /data/stage2_upscale/x.png
```

See [docs/phases/](../../docs/phases/).
