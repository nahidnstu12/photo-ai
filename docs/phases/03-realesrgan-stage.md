# Phase 3 — Real-ESRGAN Stage

**Status:** not started  
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

---

## Verification

```bash
./scripts/download-models.sh   # or documented manual wget
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

- [ ] Weights download documented and scripted
- [ ] Upscale CLI produces ~2x dimensions
- [ ] Fabric detail improved without extreme halos (visual check)
- [ ] `PIPELINE_UPSCALE` env respected
- [ ] pytest for upscale with tiny fixture (mock inference optional)

---

## Agent notes

- **deterministic mode** (Phase 5) ends here — rembg + upscale must be solid before SD.
- Anime Real-ESRGAN variants are explicitly wrong for this project — do not add.
