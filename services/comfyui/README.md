# ComfyUI service

Headless ComfyUI for SD img2img polish (phase 4).

- Image: ComfyUI **v0.3.49**, CPU default (`COMFYUI_EXTRA_ARGS=--cpu`)
- Checkpoint: `data/models/comfyui/checkpoints/realisticVision_v51.safetensors`
- Workflow: `workflows/polish_catalog.json`
- Test: `../../scripts/comfyui-prompt-test.sh`

Orchestrator client: phase 5 (`app/pipeline/polish.py`).

See [docs/phases/04-comfyui-service.md](../../docs/phases/04-comfyui-service.md).
