# rembg — background removal crash course

**In photo-ai:** Stage 1 — isolate the clothing from the background, then paste on white.

---

## What is rembg?

A Python library that uses **U2-Net** (a small neural network) to detect "foreground subject" vs "background" and output a **PNG with transparency**.

```
Input:  shirt on cluttered background (JPG)
Output: shirt only, transparent around it (PNG with alpha channel)
```

No text prompts. No randomness. Same photo → same cutout.

---

## CLI mental model (try before coding)

After install:

```bash
rembg i input.jpg output.png
# i = input file → output file
```

First run downloads ~170MB model. Later runs: few seconds on CPU.

**Clothing-specific model (we use this):**

```bash
rembg i -m u2net_cloth_seg input.jpg output.png
```

`u2net_cloth_seg` is trained on clothing silhouettes — fewer cases where sleeves/collars get chopped.

---

## Python API (what our pipeline wraps)

```python
from rembg import remove
from PIL import Image
import io

def remove_background(input_path: str, output_path: str, model: str = "u2net_cloth_seg"):
    with open(input_path, "rb") as f:
        raw = f.read()

    # AI cutout → bytes of PNG with transparency
    result_bytes = remove(raw, session=...)  # session caches model

    img = Image.open(io.BytesIO(result_bytes)).convert("RGBA")
    img.save(output_path, "PNG")
```

`remove()` returns image bytes — not a file path.

---

## Step 2 in our pipeline: white composite

rembg gives **transparent** background. Catalog wants **white**.

```python
from PIL import Image

def composite_on_white(rgba_path: str, output_path: str):
    img = Image.open(rgba_path).convert("RGBA")
    white = Image.new("RGBA", img.size, (255, 255, 255, 255))
    final = Image.alpha_composite(white, img).convert("RGB")
    final.save(output_path, "PNG")
```

Think: stack white paper under the cutout sticker.

---

## Visual mental model

```
BEFORE                          AFTER rembg              AFTER composite
┌──────────────────┐           ┌──────────────┐         ┌──────────────┐
│ ░░bed░░░░░░░░░░░ │           │              │         │              │
│ ░░┌────────┐░░░░ │    →      │  ┌────────┐  │   →     │  ┌────────┐  │
│ ░░│ shirt  │░░░░ │           │  │ shirt  │  │         │  │ shirt  │  │
│ ░░└────────┘░░░░ │           │  └────────┘  │         │  └────────┘  │
└──────────────────┘           └──────────────┘         │  white bg    │
                          (checkerboard = transparent)   └──────────────┘
```

---

## Common failures (and fixes)

| Problem | Likely cause | Fix |
|---------|--------------|-----|
| Sleeve missing | Default model | Use `u2net_cloth_seg` |
| White shirt on white wall vanishes | Low contrast | Manual mask later (Phase 7); try different photo |
| Jagged edges | Normal for AI cutout | ESRGAN + light SD polish can help |
| Slow first run | Model download | Cache in `data/models/rembg/` |

---

## In Docker (photo-ai)

- rembg runs **inside orchestrator container** (Phase 2)
- Model cache on volume so rebuild doesn't re-download
- Env: `REMBG_MODEL=u2net_cloth_seg`

---

## What rembg does NOT do

- Fix lighting
- Upscale resolution
- Remove wrinkles
- Change background to grey/lifestyle scenes (we only composite white in MVP)

Those are later stages (ESRGAN / ComfyUI).

---

## Mini exercise (when Phase 2 is done)

```bash
docker compose exec orchestrator python -m app.cli stage rembg \
  --input /data/input/shirt.jpg \
  --output /data/stage1_nobg/shirt.png
```

Open `data/stage1_nobg/shirt.png` — if cutout looks good, move on to upscale.

---

## Next

[03-realesrgan.md](./03-realesrgan.md) — make it bigger and sharper without changing the design.
