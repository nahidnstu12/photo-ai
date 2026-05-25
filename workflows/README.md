# ComfyUI API workflows

Place **Export (API)** JSON files here — not UI workflow format.

## `polish_catalog.json` (committed)

img2img catalog polish — realisticVision v5.1, denoise **0.30**.

| Node ID | class_type | Notes |
|---------|------------|-------|
| 1 | LoadImage | expects `input.png` in ComfyUI `input/` folder |
| 2 | CheckpointLoaderSimple | `realisticVision_v51.safetensors` |
| 3 | CLIPTextEncode | positive (catalog prompts) |
| 4 | CLIPTextEncode | negative |
| 5 | VAEEncode | img2img latent |
| 6 | KSampler | steps 20, CFG 7, `dpmpp_2m_sde`, denoise 0.3 |
| 7 | VAEDecode | |
| 8 | SaveImage | prefix `photo_ai_polish` → `output/` |

Manual test: [scripts/comfyui-prompt-test.sh](../scripts/comfyui-prompt-test.sh)

## Phase 5 overrides

Orchestrator `polish.py` should override these node inputs:

| Parameter | Node ID | Field |
|-----------|---------|-------|
| denoise | 6 | `inputs.denoise` |
| seed | 6 | `inputs.seed` |
| positive prompt | 3 | `inputs.text` |
| negative prompt | 4 | `inputs.text` |
| input image | 1 | `inputs.image` (or ComfyUI upload API) |

Default prompts: [docs/glossary.md](../docs/glossary.md).
