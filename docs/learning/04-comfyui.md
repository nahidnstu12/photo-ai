# ComfyUI + Stable Diffusion — crash course

**In photo-ai:** Stage 4 (optional) — light **img2img** polish for studio lighting. This is the **generative** part — misconfigure it and the shirt color shifts.

---

## What is Stable Diffusion (SD)?

A large AI model that generates/edits images from **text prompts**. Trained on millions of image-caption pairs.

**txt2img:** noise → image from scratch  
**img2img:** existing image + prompt → modified image ← **we use this**

---

## What is ComfyUI?

A **visual node editor** that runs Stable Diffusion — but we don't click nodes in production.

```
Dev time:  Build workflow in browser → Export API JSON
Run time:  Python POSTs JSON to ComfyUI → get image back
```

ComfyUI = **SD runtime server** with an HTTP API (`/prompt`).

---

## The one knob you must understand: denoise

In img2img, **denoise** = how much SD replaces your pixels.

| denoise | What happens | Catalog use? |
|---------|--------------|--------------|
| 0.1 | Barely changes | Minor cleanup only |
| **0.25–0.35** | Even lighting, cleaner bg | ✅ **Our default (0.30)** |
| 0.5 | Noticeable color/pattern drift | Risky |
| 0.8 | New image inspired by old | ❌ Never for products |

**If the stripe pattern on a shirt changes → denoise was too high.**

---

## Other settings (defaults in photo-ai)

| Setting | Value | Meaning |
|---------|-------|---------|
| steps | 20 | How many refinement iterations (more = slower, diminishing returns) |
| CFG | 7 | How hard to follow the text prompt |
| sampler | DPM++ 2M Karras | Algorithm for steps — good default for product shots |
| checkpoint | realisticVision v5.1 | The SD "brain" — tuned for realistic photos |

---

## Prompts (text instructions)

**Positive** — what you want:

```
product photography, clothing on white background, studio lighting,
sharp fabric texture, professional ecommerce catalog, even lighting,
clean background, commercial photography
```

**Negative** — what to avoid:

```
mannequin, person, wrinkle, blur, watermark, plastic, dark background
```

Prompts live in the ComfyUI workflow JSON; orchestrator can override them per job (Phase 5).

---

## ComfyUI node graph (minimal)

You don't hand-draw this every time — export once as JSON:

```
[Load Checkpoint] ──► [Load Image] ──► [KSampler] ──► [VAE Decode] ──► [Save Image]
                           ▲              ▲
                    your upscaled    denoise=0.3
                    shirt PNG        + prompts
```

**KSampler** = where the AI actually runs.

---

## API flow (what `polish.py` does)

```
1. Load workflows/polish_catalog.json
2. Upload image OR set path ComfyUI can read
3. POST http://comfyui:8188/prompt  { "prompt": workflow }
4. ComfyUI returns prompt_id
5. Poll GET /history/{prompt_id} until done
6. Download output image → data/stage3_sd/shirt.png
7. Save final JPG → data/output/shirt.jpg
```

**curl sketch (simplified):**

```bash
curl -X POST http://localhost:8188/prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": { ... node graph ... }}'
```

Our Python client hides this.

---

## Why ComfyUI is a separate Docker service

- **Huge dependencies** (~2–4 GB checkpoint)
- **Crashes / OOM** more often than rembg
- **GPU hungry** — SD img2img uses ~7–8 GB RAM peak
- Restart ComfyUI without restarting FastAPI

---

## Mac M4 practical note

Docker on Mac **cannot use Apple GPU (MPS)** inside containers well.

**Hybrid dev (common):**

```
ComfyUI  → run natively on Mac (fast, MPS)
FastAPI  → Docker (calls host.docker.internal:8188)
```

Set in `.env`:

```
COMFYUI_URL=http://host.docker.internal:8188
```

---

## Workflow files

| File | Purpose |
|------|---------|
| `workflows/polish_catalog.json` | API export — committed to git |
| `*.safetensors` checkpoint | **Not** in git — download to volume |

Export from UI: **Workflow → Export (API)** — not the normal save format.

---

## When to skip ComfyUI entirely

Use `pipeline_mode=deterministic`:

```
rembg → white composite → Real-ESRGAN → done
```

Good enough for many listings. Add SD when lighting is visibly uneven.

---

## Red flags (SD misconfiguration)

| Symptom | Likely cause |
|---------|--------------|
| Color shifted | denoise > 0.35 |
| Pattern changed | denoise too high or wrong checkpoint |
| Plastic look | prompt says "8k, ultra sharp" |
| OOM crash | need `--force-fp16`, one image at a time |
| 2 min+ on Mac Docker CPU | expected — use hybrid/native ComfyUI |

---

## ComfyUI vs rembg vs ESRGAN (summary)

| | rembg | Real-ESRGAN | ComfyUI |
|---|-------|-------------|---------|
| Type | Cutout | Upscale | Generative edit |
| Prompts? | No | No | Yes |
| Random? | No | No | Yes (seed) |
| Risk to design | Low | Low | **Medium** if denoise high |

---

## Mini exercise (Phase 4–5)

1. Open `http://localhost:8188` — confirm ComfyUI UI loads (dev only)
2. Run full pipeline:

```bash
curl -X POST http://localhost:8090/api/v1/enhance \
  -F "file=@data/input/shirt.jpg" \
  -F "pipeline_mode=full" \
  -F "denoise=0.30"
```

3. Compare `stage2_upscale/` vs `stage3_sd/` vs `output/` — SD should subtly even lighting, not redesign the shirt.

---

## Next

[05-putting-it-together.md](./05-putting-it-together.md) — one image through the full system.
