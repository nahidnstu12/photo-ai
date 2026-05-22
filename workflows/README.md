# ComfyUI API workflows

Place **Export (API)** JSON files here — not UI workflow format.

## Required (Phase 4)

| File | Purpose |
|------|---------|
| `polish_catalog.json` | img2img catalog polish — KSampler denoise 0.30 |

## Node injection (Phase 5)

When the orchestrator overrides parameters, document node IDs here after export:

| Parameter | Node ID | Field |
|-----------|---------|-------|
| denoise | TBD | inputs.denoise |
| seed | TBD | inputs.seed |
| positive prompt | TBD | inputs.text |
| negative prompt | TBD | inputs.text |
| input image | TBD | inputs.image |

Export from ComfyUI: **Workflow → Export (API)** (Ctrl+Shift+E).

Default prompts: see [docs/glossary.md](../docs/glossary.md).
