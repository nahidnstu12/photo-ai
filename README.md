# photo-ai

Local **Docker-based** product photo enhancement pipeline — raw clothing photo → catalog-ready image.

**No cloud APIs.** Stack: Python · rembg · Real-ESRGAN · ComfyUI (SD img2img).

---

## Status

**Planning complete — implementation starts at Phase 1.**

| Doc | Description |
|-----|-------------|
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
docker compose build
docker compose up -d
curl http://localhost:8090/health
```

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
