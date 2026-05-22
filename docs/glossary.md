# Glossary

| Term | Definition |
|------|------------|
| **Catalog-ready** | White/grey background, even lighting, sharp enough for e-commerce listing (~1500px+ long edge) |
| **ComfyUI** | Node-based Stable Diffusion runner; we use API JSON workflows, not manual UI clicks |
| **Composite** | Paste RGBA subject onto solid studio background (white default) |
| **denoise** | img2img strength 0.0–1.0; how much SD changes the input. Catalog sweet spot: **0.25–0.35** |
| **deterministic mode** | Pipeline runs rembg + ESRGAN only; skips ComfyUI |
| **full mode** | All stages including SD polish |
| **CFG scale** | Classifier-free guidance; how hard SD follows prompt. Default **7** |
| **img2img** | SD mode that starts from an existing image rather than random noise |
| **KSampler** | ComfyUI node that runs the diffusion steps |
| **Orchestrator** | FastAPI service that runs pipeline stages in order |
| **realisticVision v5.1** | Default SD checkpoint for fabric/product realism |
| **rembg** | Background removal using U2-Net family models |
| **Stage artifact** | Intermediate file written under `data/stageN_*` for debugging |
| **u2net_cloth_seg** | rembg model trained for clothing silhouettes — preferred over default |
| **Real-ESRGAN x4plus** | Upscale model; use at **2x outscale** for natural fabric texture |
| **Workflow (API JSON)** | ComfyUI export for `/prompt` — not the visual UI workflow format |
| **Aesthetic preset** | Named prompt variant (minimal, luxury, lifestyle, studio, dark) — Phase 7 |

## Quality levers (quick reference)

| Problem | Lever |
|---------|-------|
| Garment color drift | Lower denoise to 0.2 |
| Over-sharp fabric | Reduce upscale to 2x; remove "8k" from prompts |
| Bad cutout on clothes | `u2net_cloth_seg` model |
| ComfyUI OOM | `--force-fp16`, taesd VAE, one image at a time |
| Plastic/over-processed look | Shorten positive prompt; lower denoise |

## Prompt tokens (catalog default)

**Positive:** product photography, clothing on white background, studio lighting, sharp fabric texture, professional ecommerce catalog, even lighting, clean background, commercial photography

**Negative:** mannequin, person, model, shadow, wrinkle, crease, noise, blur, logo, watermark, text, low quality, distorted, artifacts, dark background, colorful background, plastic, shiny
