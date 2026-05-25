# Phase 3 — Real-ESRGAN Stage

**Status:** complete  
**Depends on:** [Phase 2](./02-rembg-stage.md)  
**Parallel with:** [Phase 4](./04-comfyui-service.md)

---

## Goal

2x upscale stage sharpens fabric texture from rembg output — deterministic, no SD.

---

## Scope IN

- Download script: `scripts/download-models.sh` for `RealESRGAN_x4plus.pth`
- Mount weights at `data/models/realesrgan/` or named volume
- `app/pipeline/upscale.py` — 2x outscale via realesrgan Python API or controlled subprocess
- CLI: `python -m app.cli stage upscale --input PATH --output PATH`
- Output to `data/stage2_upscale/{basename}.png`
- Chain test CLI: `stage rembg && stage upscale` (two commands, not full pipeline yet)

## Scope OUT

- ComfyUI / SD polish
- 4x upscale (locked: 2x for fabric)
- GPU in orchestrator (CPU OK for MVP; document slowness)

---

## Implementation notes

- Model file: `RealESRGAN_x4plus.pth` from xinntao releases (~64MB)
- **outscale=2** even though model name says x4plus
- If over-sharpened, expose `UPSCALE_SCALE` env (default 2)

```python
# upscale.py — contract
def run(input_path: Path, output_path: Path, *, scale: int = 2) -> None:
    ...
```

Prefer Python package `realesrgan` over shelling to repo script unless simpler.

### As implemented

| Piece | Detail |
|-------|--------|
| Module | `app/pipeline/upscale.py` |
| CLI | `python -m app.cli stage upscale --input … --output …` |
| Weights | `data/models/realesrgan/RealESRGAN_x4plus.pth` |
| Deps | `torch==2.1.2`, `torchvision==0.16.2`, `numpy<2`, `basicsr==1.4.2`, `realesrgan==0.3.0` |
| Tiling | `tile=0` if ≤1.5M px else `tile=256` (Docker RAM) |
| Validation | Rejects weights &lt;1MB (catches bad `Not Found` downloads) |

### Troubleshooting

| Symptom | Fix |
|---------|-----|
| `_pickle.UnpicklingError: could not find MARK` | Re-download weights (v0.1.0 URL); file must be ~64MB |
| `functional_tensor` import error | Rebuild orchestrator — torchvision must be &lt;0.17 |
| NumPy errors with torch | Rebuild — `numpy<2` pinned in image |
| Exit 137 / OOM | Increase Docker RAM; large images use many tiles (~minutes on CPU) |
| stage2 not 2× stage1 | Rerun upscale after fixing stage1 (stale output from old rembg) |

---

## Verification

```bash
# Download weights yourself (see README "Model downloads")
curl -fL -o data/models/realesrgan/RealESRGAN_x4plus.pth \
  https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth
docker compose build orchestrator
docker compose up -d
docker compose exec orchestrator python -m app.cli stage rembg \
  --input /data/input/sample.jpg --output /data/stage1_nobg/sample.png
docker compose exec orchestrator python -m app.cli stage upscale \
  --input /data/stage1_nobg/sample.png --output /data/stage2_upscale/sample.png
identify data/stage2_upscale/sample.png   # dimensions ~2x stage1
```

---

## Done when

- [x] Weights download documented and scripted
- [x] Upscale CLI produces ~2x dimensions
- [x] Fabric detail improved without extreme halos (visual check)
- [x] `PIPELINE_UPSCALE` env respected
- [x] pytest for upscale with tiny fixture (mock inference optional)

---

## Agent notes

- **deterministic mode** (Phase 5) ends here — rembg + upscale must be solid before SD.
- Anime Real-ESRGAN variants are explicitly wrong for this project — do not add.
