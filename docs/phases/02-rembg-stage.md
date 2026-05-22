# Phase 2 — rembg Stage

**Status:** not started  
**Depends on:** [Phase 1](./01-docker-foundation.md)  
**Parallel with:** [Phase 4](./04-comfyui-service.md) (after Phase 1)

---

## Goal

Background removal + white canvas composite works as an isolated pipeline stage via CLI and API stub.

---

## Scope IN

- Add `rembg[cli]`, `onnxruntime`, `Pillow` to orchestrator image
- `app/pipeline/remove_bg.py` — rembg with configurable model (default `u2net_cloth_seg`)
- `app/pipeline/composite.py` — RGBA → RGB on white (255,255,255)
- CLI: `python -m app.cli stage rembg --input PATH --output PATH`
- Write output to `data/stage1_nobg/{basename}.png`
- Optional: `POST /api/v1/stages/rembg` (single-stage endpoint for testing)
- Unit test with tiny fixture PNG (solid shape on colored bg)

## Scope OUT

- Real-ESRGAN, ComfyUI
- Batch runner
- Aesthetic presets

---

## Implementation notes

```python
# remove_bg.py — contract
def run(input_path: Path, output_path: Path, *, model: str = "u2net_cloth_seg") -> None:
    ...
```

- Cache rembg models in volume `rembg_models` or `data/models/rembg/` to avoid re-download
- On first run, model download ~170MB — log clearly
- If cutout fails (empty alpha), raise `StageError` with actionable message

### Composite edge cases (from guide)

- Prefer `alpha_composite` for default; document `paste()` fallback for same-color garment edges in Phase 7

---

## Verification

```bash
# Place a test JPG in data/input/sample.jpg
docker compose build orchestrator
docker compose up -d
docker compose exec orchestrator python -m app.cli stage rembg \
  --input /data/input/sample.jpg \
  --output /data/stage1_nobg/sample.png
# Inspect: transparent subject or white-bg RGB PNG
file data/stage1_nobg/sample.png
```

Compare visually: subject intact, background white, no major garment clipping.

---

## Done when

- [ ] CLI stage completes on sample clothing image
- [ ] Output saved under `data/stage1_nobg/`
- [ ] Model configurable via `REMBG_MODEL` env
- [ ] Test passes in CI/local `pytest`
- [ ] Stage completes in <10s on sample (CPU acceptable)

---

## Agent notes

- Do not chain to upscale in this phase — single stage only.
- Pin rembg/onnxruntime versions in `pyproject.toml` after first successful build.
