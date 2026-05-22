# photo-ai — Master Plan

**Status:** planning  
**Stack:** Docker Compose · Python 3.11 · rembg · Real-ESRGAN · ComfyUI

---

## Objective

Ship a **containerized, API-driven pipeline** that converts raw clothing product photos into polished catalog images with:

- Deterministic stages where possible (rembg, ESRGAN)
- Controlled generative polish (SD img2img at low denoise)
- Batch processing and stage artifact retention for debugging
- No cloud API dependency

---

## Locked-in decisions

| # | Decision | Consequence |
|---|----------|-------------|
| 1 | **Docker Compose** is the runtime | No bare-metal venv as primary path; docx Mac setup is reference only |
| 2 | **ComfyUI as separate service** | Orchestrator calls HTTP API; workflows live in `workflows/` as JSON |
| 3 | **Incremental stages** | Each stage writes to disk under `data/stageN_*` before next runs |
| 4 | **Catalog-safe defaults** | denoise 0.30, upscale 2x, rembg `u2net_cloth_seg` |
| 5 | **SD polish is optional per job** | `pipeline_mode=deterministic` skips ComfyUI (rembg + ESRGAN only) |
| 6 | **Models not in git** | Volume-mounted; documented download scripts in Phase 4 |
| 7 | **Python 3.11** in orchestrator | 3.12 excluded until deps support it |
| 8 | **Garment fidelity over aesthetics** | No beautifier/expand/uncrop in MVP |
| 9 | **FastAPI orchestrator** | REST + CLI entrypoint share same pipeline module |
| 10 | **Checkpoint: realisticVision v5.1** | Default SD model; others via config |

---

## Architecture (one diagram)

```
                    ┌─────────────────────────────────────┐
  data/input/       │         orchestrator :8090          │
  (raw JPG/PNG) ──► │  FastAPI + pipeline runner          │
                    │    ├─ stage1: rembg               │
                    │    ├─ stage2: composite (PIL)       │
                    │    ├─ stage3: Real-ESRGAN 2x        │
                    │    └─ stage4: ComfyUI client ───────┼──► comfyui :8188
                    └─────────────────────────────────────┘              │
                              │                                          │
                              ▼                                          ▼
                    data/stage1_nobg/ … stage3_sd/          workflows/*.json
                    data/output/  (final JPG)
```

Phase 6 adds **Redis + async jobs**; Phase 7 adds quality gates and ops.

---

## Phase sequence

Each phase is ** independently verifiable**. Do not skip ahead.

| Phase | File | Depends on | Delivers |
|-------|------|------------|----------|
| 1 | [01-docker-foundation.md](./phases/01-docker-foundation.md) | — | Compose shell, health endpoints, data dirs |
| 2 | [02-rembg-stage.md](./phases/02-rembg-stage.md) | 1 | Background removal + white composite |
| 3 | [03-realesrgan-stage.md](./phases/03-realesrgan-stage.md) | 2 | 2x upscale stage |
| 4 | [04-comfyui-service.md](./phases/04-comfyui-service.md) | 1 | ComfyUI container + workflow + model mount |
| 5 | [05-orchestrator-api.md](./phases/05-orchestrator-api.md) | 2, 3, 4 | Full pipeline API + CLI |
| 6 | [06-batch-queue.md](./phases/06-batch-queue.md) | 5 | Redis queue, batch runner, job status |
| 7 | [07-ops-quality.md](./phases/07-ops-quality.md) | 6 | Preflight checks, presets, monitoring |

**Parallel work:** Phase 4 (ComfyUI) can start once Phase 1 is done — parallel with Phase 2–3.

---

## Folder structure (target)

```
photo-ai/
├── .cursor/rules/
├── docs/
├── services/
│   ├── orchestrator/
│   └── comfyui/              # Dockerfile + entrypoint only
├── workflows/
│   └── polish_catalog.json   # ComfyUI API export
├── scripts/
│   └── download-models.sh
├── data/                     # gitignored
│   ├── input/
│   ├── output/
│   ├── stage1_nobg/
│   ├── stage2_upscale/
│   ├── stage3_sd/
│   └── models/
├── docker-compose.yml
├── docker-compose.gpu.yml
├── .env.example
└── photo_enhancement_guide.docx
```

---

## Non-goals (MVP)

- Web UI for manual editing
- Multi-tenant auth
- Cloud deployment (K8s) — defer to post-MVP
- OCR / product attribute extraction
- Automatic garment color correction without human review option
- Automatic1111 integration (use ComfyUI only)

---

## Success criteria (project complete)

1. `POST /api/v1/enhance` accepts image, returns job id or sync result
2. Batch: drop N images in `data/input/`, run CLI, get N catalog JPGs in `data/output/`
3. `pipeline_mode=deterministic` produces acceptable output for 80%+ test set without SD
4. Full pipeline completes on reference hardware within documented time bounds
5. All phases have passing verification commands documented

---

## Agent entry point

When starting work:

1. Read this file
2. Open the **lowest-numbered incomplete** phase in `docs/phases/`
3. Complete only that phase's scope
4. Run verification commands from that phase
5. Check off deliverables in the phase doc

See [agent-guidelines.md](./agent-guidelines.md) for detailed rules.
