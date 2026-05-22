# Learning — crash course

**Goal:** Understand the photo-ai stack enough to read the code, run the pipeline, and debug stages — **not** become an ML researcher.

Read in order (≈45–60 min total):

| # | Doc | Time | You'll understand |
|---|-----|------|-------------------|
| 0 | [00-big-picture.md](./00-big-picture.md) | 10 min | Why 4 tools, pipeline flow, deterministic vs generative |
| 1 | [01-fastapi.md](./01-fastapi.md) | 10 min | Orchestrator API, how requests trigger stages |
| 2 | [02-rembg.md](./02-rembg.md) | 8 min | Background removal, clothing model |
| 3 | [03-realesrgan.md](./03-realesrgan.md) | 8 min | Upscaling without changing the design |
| 4 | [04-comfyui.md](./04-comfyui.md) | 15 min | SD img2img, denoise, workflows, API |
| 5 | [05-putting-it-together.md](./05-putting-it-together.md) | 5 min | End-to-end walkthrough with one sample image |

---

## Mental model (one sentence each)

| Tool | One-liner |
|------|-----------|
| **FastAPI** | The **conductor** — receives photos, runs stages in order, returns results |
| **rembg** | The **scissors** — cuts the shirt/pants out of the messy background |
| **Real-ESRGAN** | The **magnifying glass** — makes the image bigger and sharper (same design) |
| **ComfyUI** | The **lighting assistant** — gently fixes lighting/colors using AI (can drift if misconfigured) |

---

## When you're stuck

| Symptom | Read |
|---------|------|
| "What calls what?" | [00-big-picture.md](./00-big-picture.md) |
| "API / Docker / health check?" | [01-fastapi.md](./01-fastapi.md) |
| "Cutout eats the sleeve" | [02-rembg.md](./02-rembg.md) |
| "Fabric looks crunchy/over-sharp" | [03-realesrgan.md](./03-realesrgan.md) |
| "Colors/pattern changed" | [04-comfyui.md](./04-comfyui.md) — denoise too high |
| "Full pipeline debug" | [05-putting-it-together.md](./05-putting-it-together.md) |

---

## After learning

- Implementation: [../phases/](../phases/) (phase by phase)
- Reference terms: [../glossary.md](../glossary.md)
- System design: [../architecture.md](../architecture.md)

Original deep-dive source (Mac-native): `../../photo_enhancement_guide.docx`
