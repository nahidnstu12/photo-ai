# Phase 1 — Docker Foundation

**Status:** not started  
**Depends on:** —  
**Parallel with:** —

---

## Goal

`docker compose up` starts a healthy **orchestrator** shell and **data volume layout** — no ML stages yet.

---

## Scope IN

- `docker-compose.yml` with `orchestrator` (+ stub `comfyui` optional "not ready" or comment-only)
- `services/orchestrator/Dockerfile` (Python 3.11 slim)
- FastAPI app: `GET /health` → `{ "status": "ok", "phase": 1 }`
- `services/orchestrator/pyproject.toml` with fastapi, uvicorn, pydantic-settings
- `.env.example`, `.gitignore`
- Create `data/` directory structure (empty `.gitkeep` files)
- README quickstart section

## Scope OUT

- rembg, Real-ESRGAN, ComfyUI implementation
- Model downloads
- Pipeline logic

---

## Deliverables

| Path | Description |
|------|-------------|
| `docker-compose.yml` | orchestrator service, ports, volumes |
| `services/orchestrator/Dockerfile` | Multi-stage or slim Python 3.11 |
| `services/orchestrator/app/main.py` | FastAPI + `/health` |
| `services/orchestrator/app/config.py` | `DATA_DIR`, env loading |
| `data/input/.gitkeep` | etc. for all data subdirs |
| `README.md` | Prerequisites, compose commands, Mac hybrid note |

---

## Mac / GPU note (document in README)

Docker on Mac **does not expose MPS**. For M4 dev, document **Mode B (hybrid)** in [architecture.md](../architecture.md):

- Phase 1–3: orchestrator in Docker is fine (CPU)
- Phase 4+: ComfyUI may run natively on host for speed

---

## Verification

```bash
cd photo-ai
cp .env.example .env
docker compose build orchestrator
docker compose up -d
docker compose ps                    # orchestrator healthy
curl -sf http://localhost:8090/health | jq .
docker compose logs orchestrator     # no crash loop
```

---

## Done when

- [ ] `docker compose up -d` succeeds from clean clone (no models needed)
- [ ] `/health` returns 200 JSON
- [ ] `./data/input`, `output`, `stage1_nobg`, `stage2_upscale`, `stage3_sd`, `models` exist
- [ ] `.env.example` documents all vars (even if unused until later phases)
- [ ] README explains Docker vs hybrid Mac dev

---

## Agent notes

- Use `platform: linux/amd64` only if arm64 build fails — prefer native arm64 on M4.
- Bind mount `./data:/data` consistently — all later phases assume `/data` inside container.
- Keep orchestrator Dockerfile under 200 lines; no ML deps in Phase 1.
