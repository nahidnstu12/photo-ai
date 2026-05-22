# Big picture — how photo-ai works

Before FastAPI, rembg, or ComfyUI details: **what problem we solve** and **why four tools**.

---

## The problem

You have a photo like this (conceptually):

```
📷 Phone photo of a shirt on a bed / mannequin / messy shop floor
   - Busy background
   - Uneven lighting
   - Maybe only 800px wide
```

You need this for an online store:

```
🛍️ Shirt on clean white background
   - Even studio-like lighting
   - Sharp fabric texture
   - ~1500px+ for zoom on product page
```

**photo-ai** automates that transformation locally (no Photoroom API).

---

## The pipeline (5 steps)

```
┌─────────┐   ┌───────┐   ┌───────────┐   ┌────────────┐   ┌─────────┐   ┌────────┐
│  YOU    │   │ rembg │   │ composite │   │ Real-ESRGAN│   │ ComfyUI │   │  JPG   │
│ upload  │──►│ cutout│──►│ white bg  │──►│  2x bigger │──►│ polish  │──►│ output │
└─────────┘   └───────┘   └───────────┘   └────────────┘   └─────────┘   └────────┘
                  │              │                │                │
             deterministic   deterministic    deterministic     generative
             (same in,       (PIL math)       (neural upscale)  (AI can drift)
              same out)
```

| Step | Tool | Changes the garment design? |
|------|------|----------------------------|
| 1. Cutout | rembg | No — only removes background |
| 2. White background | Python PIL | No — paste on white |
| 3. Upscale | Real-ESRGAN | No — sharper/bigger pixels |
| 4. Polish | ComfyUI + Stable Diffusion | **Maybe** — if denoise too high |

That's why we have **`deterministic` mode** (steps 1–3 only) and **`full` mode** (adds step 4).

---

## Two kinds of AI in this project

### Type A — Deterministic (safe for catalog)

Same input → same output every time.

- **rembg:** "Find the subject, delete everything else"
- **Real-ESRGAN:** "Predict higher-res pixels from low-res"

Good when: you must not change logo, pattern, or color of the clothing.

### Type B — Generative (powerful but risky)

Uses **Stable Diffusion** — a model trained on millions of images. It *imagines* pixels.

- **ComfyUI** runs SD in **img2img** mode: start from your photo + text prompt → refined photo
- **denoise** (0.0–1.0) = how much it re-imagines
  - `0.3` → light polish ✅
  - `0.7` → new shirt ❌ (for catalog)

**Rule of thumb:** Start without ComfyUI. Add it only when rembg + upscale isn't enough.

---

## Where FastAPI fits

FastAPI doesn't touch pixels. It's the **orchestrator**:

```
Client (curl / CLI / future app)
        │
        ▼
   FastAPI  POST /api/v1/enhance
        │
        ├── call rembg stage      → save data/stage1_nobg/
        ├── call composite        → in memory
        ├── call Real-ESRGAN      → save data/stage2_upscale/
        └── call ComfyUI API      → save data/stage3_sd/ → data/output/
        │
        ▼
   JSON response { output_path, artifacts, duration_ms }
```

Think: **FastAPI = recipe card**. rembg/ESRGAN/ComfyUI = **kitchen appliances**.

---

## Where Docker fits

Each appliance has heavy dependencies (Python packages, GB-sized models). Docker:

- Packages them so your Mac/Linux runs the same stack
- Mounts `./data` for input/output
- Runs ComfyUI as a **separate container** (it crashes/restarts independently)

**Mac caveat:** Docker containers can't use Apple GPU (MPS) easily. Often ComfyUI runs **on the host** for speed; FastAPI stays in Docker. See [architecture.md](../architecture.md).

---

## Files on disk (why stages matter)

```
data/
├── input/shirt.jpg           ← you drop this
├── stage1_nobg/shirt.png     ← after rembg (debug: is cutout OK?)
├── stage2_upscale/shirt.png  ← after upscale (debug: too sharp?)
├── stage3_sd/shirt.png       ← after ComfyUI (debug: color drift?)
└── output/shirt.jpg          ← final
```

If final looks wrong, **open the stage folder** — you'll know which tool to blame.

---

## What you don't need to learn (for this project)

- Training ML models
- Stable Diffusion theory / latent diffusion math
- ComfyUI node graph UI mastery (we export JSON once, automate via API)
- Kubernetes, cloud GPU providers

---

## Next

[01-fastapi.md](./01-fastapi.md) — the orchestrator you'll actually curl and extend.
