# Agent Guidelines

Instructions for AI coding agents working in **photo-ai**.

---

## Before you write code

1. Read [00-plan.md](./00-plan.md) — locked decisions are not negotiable unless the user explicitly changes them.
2. Identify the **current phase** — only implement what that phase file scopes.
3. Read [.cursor/rules/core.mdc](../.cursor/rules/core.mdc) and the file-specific rule for what you're editing.
4. Check existing code under `services/` — extend, don't duplicate.

---

## Phase discipline

Each phase doc has:

- **Goal** — one sentence
- **Scope IN / OUT** — hard boundaries
- **Deliverables** — files and behaviors that must exist
- **Verification** — exact commands; run them before marking done
- **Done when** — checklist

**Rules:**

- Do not add ComfyUI integration before Phase 4/5.
- Do not add Redis before Phase 6.
- Do not add a web UI unless scoped in a future phase.
- If blocked (missing model, GPU), document in phase checklist and stop — don't workaround with cloud APIs.

---

## Code quality

- **Python 3.11**, type hints, pydantic-settings for config
- One module per pipeline stage under `app/pipeline/`
- Tests for stage modules with fixture images (small PNG in `tests/fixtures/`)
- No `any` in Python; no committed secrets
- Docker: healthchecks on every long-running service

---

## Pipeline safety (catalog mode)

These defaults protect garment fidelity:

| Setting | Max safe | Never in MVP |
|---------|----------|--------------|
| denoise | 0.35 | > 0.45 |
| upscale | 2x | 4x for fabric |
| SD features | img2img polish only | beautifier, uncrop, expand |

If adding a new stage that modifies pixels generatively, require explicit user approval and a feature flag.

---

## Documentation updates

When completing a phase:

- Check off **Done when** items in that phase file
- Update [00-plan.md](./00-plan.md) phase table status if you add a Status column note
- Do **not** create new top-level docs unless the user asks — update existing phase files

---

## Common mistakes to avoid

| Mistake | Why it's bad |
|---------|----------------|
| Baking SD checkpoints into Docker image | 4GB+ layers, slow rebuilds |
| Skipping stage artifact dirs | Can't debug rembg vs ESRGAN vs SD failures |
| Hardcoding ComfyUI node IDs without workflow file | Breaks when workflow is re-exported |
| Using Python 3.12 | rembg/onnx deps break |
| Running full pipeline before rembg alone is verified | Can't isolate failures |
| Exposing port 8188 on `0.0.0.0` in production docs without warning | ComfyUI has no auth |

---

## Verification pattern

Every phase should end with commands like:

```bash
docker compose build orchestrator
docker compose up -d
docker compose ps   # all healthy
curl -sf http://localhost:8090/health
# phase-specific test, e.g.:
docker compose exec orchestrator python -m app.cli stage rembg --input /data/input/sample.jpg
```

Agent must run verification or tell the user exactly what failed.

---

## Asking the user

Ask only when:

- Phase scope is ambiguous vs an explicit user request
- Model checkpoint choice differs from locked decision (realisticVision v5.1)
- GPU mode (full Docker vs hybrid Mac) affects implementation

Do not ask about stylistic choices already in locked decisions.

---

## Reference material

- `photo_enhancement_guide.docx` — concepts, prompts, KSampler settings
- [glossary.md](./glossary.md) — denoise, CFG, rembg models
- [architecture.md](./architecture.md) — service boundaries
