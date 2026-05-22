# Real-ESRGAN — upscale crash course

**In photo-ai:** Stage 3 — increase resolution and sharpen fabric texture. **Deterministic** — should not change pattern or color.

---

## What is Real-ESRGAN?

**ESRGAN** = Enhanced Super-Resolution GAN. Plain English: a neural network trained to turn a small blurry image into a larger sharper one.

```
Input:  800 × 600 shirt on white (from rembg stage)
Output: 1600 × 1200 (2x) — same shirt, more pixels
```

It's **not** generating a new design — it's guessing high-frequency detail (thread texture, edges) from low-res input.

---

## Why we need it

Phone photos are often too small for ecommerce zoom. Marketplaces want ~1500px on the long edge.

Pipeline order matters:

```
rembg first  →  ESRGAN second
(clean subject)  (sharpen clean subject)
```

Upscaling before cutout would also sharpen background clutter — wasteful.

---

## Model we use

**RealESRGAN_x4plus.pth** — general photos, works well on fabric.

Despite "x4" in the name, we run at **2x outscale** for natural fabric look:

```bash
# Conceptual CLI (upstream repo)
python inference_realesrgan.py \
  -i input.png -o output.png \
  -n RealESRGAN_x4plus \
  --outscale 2
```

| outscale | Effect |
|----------|--------|
| 2 | ✅ Recommended — sharper, not crunchy |
| 4 | Often over-sharp on textile — avoid for catalog |

Env in photo-ai: `PIPELINE_UPSCALE=2`

---

## Deterministic = trustworthy

Same PNG in → same PNG out. No seed, no prompt.

That's why **`deterministic` pipeline mode** stops after rembg + ESRGAN — you get 80% of catalog quality with **zero generative risk**.

---

## Visual mental model

```
BEFORE (800px, soft)              AFTER (1600px, crisp edges)
┌─────────────────┐              ┌─────────────────────────┐
│  ~~shirt~~      │      →       │  sharper weave, cleaner │
│  soft edges     │              │  edges, same colors     │
└─────────────────┘              └─────────────────────────┘
```

If the **color** or **stripe pattern** changes noticeably — that's not ESRGAN, that's ComfyUI (next doc).

---

## Python integration (concept)

Our orchestrator either:

1. Calls `realesrgan` Python package directly, or
2. Subprocess to inference script

```python
def upscale(input_path: Path, output_path: Path, scale: int = 2) -> None:
    # load model once at startup (slow), reuse for batch (fast)
    run_inference(input_path, output_path, model="RealESRGAN_x4plus", outscale=scale)
```

Model file ~64MB — downloaded by `scripts/download-models.sh`, mounted at `data/models/realesrgan/`.

---

## Performance (rough)

| Hardware | ~Time for 2x |
|----------|--------------|
| Mac M4 CPU | 10–15 sec |
| NVIDIA GPU | 2–5 sec |

Slower than rembg, faster than Stable Diffusion.

---

## Common failures

| Problem | Fix |
|---------|-----|
| Halos around subject | Usually bad rembg mask — fix stage 1 first |
| Plastic/fabric looks fake | Lower outscale to 2; don't combine with aggressive SD |
| OOM | Process one image at a time; smaller input |

---

## What Real-ESRGAN does NOT do

- Remove background (rembg)
- Fix yellow lighting cast (ComfyUI img2img at low denoise)
- Add shadows or studio look (ComfyUI / compositing)

---

## Mini exercise (Phase 3)

```bash
# After rembg stage output exists:
docker compose exec orchestrator python -m app.cli stage upscale \
  --input /data/stage1_nobg/shirt.png \
  --output /data/stage2_upscale/shirt.png
```

Compare dimensions:

```bash
# Should be ~2x width/height of input
identify data/stage1_nobg/shirt.png data/stage2_upscale/shirt.png
```

---

## Next

[04-comfyui.md](./04-comfyui.md) — optional polish stage (the one that needs careful tuning).
