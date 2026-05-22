# Putting it together — end-to-end walkthrough

One sample image through the whole system. Use this when debugging or explaining the project to someone else.

---

## Scenario

You have `data/input/hoodie.jpg` — phone photo, grey wall behind, slightly dark, 1000px wide.

**Goal:** `data/output/hoodie.jpg` — white background, brighter, ~2000px, catalog-ready.

---

## Step-by-step

### 0. Start services

```bash
cp .env.example .env
docker compose up -d
curl http://localhost:8090/health
# ComfyUI too, if full mode:
curl http://localhost:8188/system_stats
```

### 1. Upload triggers FastAPI

```bash
curl -X POST http://localhost:8090/api/v1/enhance \
  -F "file=@data/input/hoodie.jpg" \
  -F "pipeline_mode=full"
```

FastAPI saves upload, calls `run_pipeline()`.

### 2. rembg — cutout

```
/data/input/hoodie.jpg  →  /data/stage1_nobg/hoodie.png
```

**Check:** Open stage1 — hoodie shape complete? Sleeves intact?  
**If no:** retry with `u2net_cloth_seg`, fix photo, or stop here.

### 3. Composite — white background

In-memory (or temp file) — RGB hoodie on white.

### 4. Real-ESRGAN — 2x upscale

```
/data/stage1_nobg/hoodie.png  →  /data/stage2_upscale/hoodie.png
```

**Check:** ~2x dimensions, sharper fabric, **same colors/pattern**.

### 5. ComfyUI — img2img polish

Orchestrator POSTs workflow + image to ComfyUI:

```
/data/stage2_upscale/hoodie.png  →  /data/stage3_sd/hoodie.png
```

Settings: denoise **0.30**, realisticVision checkpoint, catalog prompts.

**Check:** Lighting more even? Pattern still same?  
**If colors shifted:** lower denoise to 0.2 or use `deterministic` mode.

### 6. Final export

```
/data/stage3_sd/hoodie.png  →  /data/output/hoodie.jpg
```

API response:

```json
{
  "status": "completed",
  "output_path": "/data/output/hoodie.jpg",
  "artifacts": {
    "stage1_nobg": "/data/stage1_nobg/hoodie.png",
    "stage2_upscale": "/data/stage2_upscale/hoodie.png",
    "stage3_sd": "/data/stage3_sd/hoodie.png"
  },
  "duration_ms": 62000
}
```

---

## Decision tree (debugging)

```
Final looks wrong?
│
├─ Cutout bad (missing sleeve, extra bg)
│   └─ Fix rembg / retake photo → stage1_nobg/
│
├─ Blurry / low-res but cutout OK
│   └─ Fix ESRGAN / check outscale → stage2_upscale/
│
├─ Color/pattern changed
│   └─ Lower denoise or disable SD → compare stage2 vs stage3
│
└─ Lighting uneven but design OK
    └─ SD helping — maybe bump denoise slightly (max 0.35)
```

---

## deterministic vs full (when to use which)

| Mode | Stages | Use when |
|------|--------|----------|
| `deterministic` | rembg + ESRGAN | Pattern fidelity critical; good lighting already |
| `full` | + ComfyUI | Dark/uneven lighting; still need denoise ≤ 0.35 |

**Learning path recommendation:** Run `deterministic` first on 5 test photos. Only enable `full` on photos that still look flat.

---

## Who talks to whom

```
┌──────────┐     HTTP      ┌───────────────┐
│   You    │ ────────────► │   FastAPI     │
│ curl/CLI │               │ orchestrator  │
└──────────┘               └───────┬───────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │ in-process   │ in-process   │ HTTP
                    ▼              ▼              ▼
                 rembg        Real-ESRGAN      ComfyUI
                 (Python)     (Python)         (separate container)
```

---

## Time budget (M4 16GB, rough)

| Stage | Time |
|-------|------|
| rembg | 3–5 s |
| ESRGAN 2x | 10–15 s |
| SD img2img | 20–40 s |
| **Total** | ~1 min |

First image slower (model load into RAM).

---

## Vocabulary cheat sheet

| You say | Means |
|---------|-------|
| "Stage failed" | One step in pipeline errored — check `failed_stage` in response |
| "Artifact" | Intermediate PNG saved under `data/stageN_*` |
| "Workflow" | ComfyUI JSON graph for `/prompt` |
| "Checkpoint" | The `.safetensors` SD model file |
| "Denoise 0.3" | SD changes ~30% of pixels — catalog-safe zone |

---

## Where to go next

| Goal | Doc |
|------|-----|
| Implement Phase 1 | [phases/01-docker-foundation.md](../phases/01-docker-foundation.md) |
| Terms | [glossary.md](../glossary.md) |
| Architecture | [architecture.md](../architecture.md) |
| Re-read one tool | [learning/README.md](./README.md) |

You now have enough context to read the phase docs and know **why** each piece exists.
