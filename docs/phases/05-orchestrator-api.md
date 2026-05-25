# Phase 5 — Orchestrator API (Full Pipeline)

**Status:** done  
**Depends on:** Phases 2, 3, 4 (all complete)  
**Parallel with:** —

---

## Already in codebase (do not re-implement)

- `app/pipeline/remove_bg.py`, `composite.py`, `upscale.py`
- `app/cli.py` — `stage rembg`, `stage upscale`
- `POST /api/v1/stages/rembg` only (no enhance, no upscale API)
- `app/config.py` — `PIPELINE_MODE`, `PIPELINE_DENOISE`, `COMFYUI_URL`, etc.
- ComfyUI service + `workflows/polish_catalog.json`

## Implemented

- `app/pipeline/runner.py` — chain stages, artifacts, `pipeline_mode`
- `app/pipeline/polish.py` — ComfyUI copy-in → prompt → poll history → `stage3_sd/`
- `POST /api/v1/enhance` — multipart + optional `pipeline_mode`, `denoise`, `seed`
- `python -m app.cli run --input /data/input/foo.jpg [--mode full|deterministic]`
- Final JPEG `data/output/{basename}.jpg` (quality 92)

---

## Goal

Single API call and CLI command run the **full pipeline** (or deterministic subset) end-to-end.

---

## Scope IN

- `app/pipeline/runner.py` — sequential stage execution with artifact paths
- `app/pipeline/polish.py` — ComfyUI client (load workflow JSON, upload image, poll, save)
- `POST /api/v1/enhance` — multipart upload, sync response with output path
- CLI: `python -m app.cli run --input /data/input/foo.jpg`
- `pipeline_mode`: `full` | `deterministic`
- Config: denoise, seed, prompts from env + request overrides
- Final output: `data/output/{basename}.jpg` (JPEG quality ~92)

## Scope OUT

- Async jobs / Redis (Phase 6)
- Multiple aesthetic presets (Phase 7)
- Auth

---

## Pipeline runner behavior

```
for stage in enabled_stages:
    log start
    run stage → write artifact path
    on error: raise PipelineError(failed_stage=..., artifact_paths=...)
return final output path
```

Enabled stages:

| Mode | Stages |
|------|--------|
| `deterministic` | rembg → composite → upscale |
| `full` | rembg → composite → upscale → polish |

---

## ComfyUI client requirements

- Read `WORKFLOW_POLISH_PATH`
- Inject input image path (ComfyUI Load Image node — use upload API if needed)
- Override KSampler denoise + seed via workflow node IDs (document IDs in workflow README snippet)
- Poll `/history/{prompt_id}` with timeout (default 120s)
- Copy result to `data/stage3_sd/` then final JPG to `data/output/`

---

## API contract

```http
POST /api/v1/enhance
Content-Type: multipart/form-data

file: (binary)
pipeline_mode: full | deterministic  (optional, default full)
denoise: 0.30                       (optional)
seed: -1                             (optional)
```

```json
{
  "status": "completed",
  "output_path": "/data/output/sample.jpg",
  "artifacts": {
    "stage1_nobg": "/data/stage1_nobg/sample.png",
    "stage2_upscale": "/data/stage2_upscale/sample.png",
    "stage3_sd": "/data/stage3_sd/sample.png"
  },
  "duration_ms": 58000
}
```

---

## Verification

```bash
docker compose up -d
curl -sf http://localhost:8090/health

# Deterministic (no ComfyUI needed if comfyui down)
curl -X POST http://localhost:8090/api/v1/enhance \
  -F "file=@data/input/sample.jpg" \
  -F "pipeline_mode=deterministic"

# Full pipeline (comfyui must be up)
curl -X POST http://localhost:8090/api/v1/enhance \
  -F "file=@data/input/sample.jpg" \
  -F "pipeline_mode=full" \
  -F "denoise=0.30"
```

CLI:

```bash
docker compose exec orchestrator python -m app.cli run --input /data/input/sample.jpg --mode full
ls -la data/output/
```

---

## Done when

- [x] Deterministic mode works with comfyui stopped
- [x] Full mode produces final JPG with all stage artifacts
- [x] denoise override works; default 0.30
- [x] Errors report `failed_stage` without deleting prior artifacts
- [ ] End-to-end documented time (~1 min hybrid M4, or CPU bounds) — verify on your machine
- [x] Unit tests (`test_runner.py`, `test_polish.py`; full E2E remains manual/docker)

---

## Agent notes

- This is the **MVP milestone** — prioritize reliability over speed.
- Fix workflow node IDs in a small `workflows/README.md` table when injecting params.
- Do not add queue/async here — keep sync API for simplicity.
