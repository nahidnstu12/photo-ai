import json
import logging
import random
import shutil
import time
import uuid
from copy import deepcopy
from pathlib import Path

import httpx

from app.config import Settings
from app.pipeline.errors import StageError

logger = logging.getLogger(__name__)

POLL_INTERVAL_SEC = 0.5


def _resolve_seed(seed: int) -> int:
    if seed < 0:
        return random.randint(0, 2**31 - 1)
    return seed


def _load_workflow(path: Path) -> dict:
    if not path.is_file():
        raise StageError(f"Workflow not found: {path}")
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _patch_workflow(
    workflow: dict,
    *,
    image_name: str,
    settings: Settings,
    denoise: float,
    seed: int,
) -> dict:
    wf = deepcopy(workflow)
    wf["1"]["inputs"]["image"] = image_name
    wf["2"]["inputs"]["ckpt_name"] = settings.sd_checkpoint
    wf["6"]["inputs"]["denoise"] = denoise
    wf["6"]["inputs"]["seed"] = _resolve_seed(seed)
    wf["6"]["inputs"]["steps"] = settings.sd_steps
    wf["6"]["inputs"]["cfg"] = settings.sd_cfg
    wf["6"]["inputs"]["sampler_name"] = settings.sd_sampler
    return wf


def _submit_prompt(base_url: str, workflow: dict) -> str:
    client_id = str(uuid.uuid4())
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                f"{base_url.rstrip('/')}/prompt",
                json={"prompt": workflow, "client_id": client_id},
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as e:
        raise StageError(f"ComfyUI prompt failed: {e}") from e

    if data.get("node_errors"):
        raise StageError(f"ComfyUI node errors: {data['node_errors']}")
    if "error" in data:
        raise StageError(f"ComfyUI error: {data['error']}")
    prompt_id = data.get("prompt_id")
    if not prompt_id:
        raise StageError(f"ComfyUI returned no prompt_id: {data}")
    return prompt_id


def _wait_history(base_url: str, prompt_id: str, timeout_sec: int) -> dict:
    deadline = time.monotonic() + timeout_sec
    url = f"{base_url.rstrip('/')}/history/{prompt_id}"
    with httpx.Client(timeout=15.0) as client:
        while time.monotonic() < deadline:
            try:
                resp = client.get(url)
                resp.raise_for_status()
                data = resp.json()
            except httpx.HTTPError as e:
                raise StageError(f"ComfyUI history poll failed: {e}") from e
            if prompt_id in data:
                return data[prompt_id]
            time.sleep(POLL_INTERVAL_SEC)
    raise StageError(f"ComfyUI timed out after {timeout_sec}s (prompt_id={prompt_id})")


def _output_image_path(history: dict, output_dir: Path) -> Path:
    outputs = history.get("outputs") or {}
    node_out = outputs.get("8") or outputs.get(8)
    if not node_out:
        raise StageError(f"No SaveImage output in ComfyUI history: {list(outputs.keys())}")
    images = node_out.get("images") or []
    if not images:
        raise StageError("ComfyUI SaveImage node returned no images")
    meta = images[0]
    filename = meta["filename"]
    subfolder = meta.get("subfolder") or ""
    path = output_dir / subfolder / filename if subfolder else output_dir / filename
    if not path.is_file():
        raise StageError(f"ComfyUI output file missing: {path}")
    return path


def run(
    input_path: Path,
    output_path: Path,
    *,
    settings: Settings,
    denoise: float,
    seed: int,
) -> None:
    if not input_path.is_file():
        raise StageError(f"Input not found: {input_path}")

    settings.comfyui_input_dir.mkdir(parents=True, exist_ok=True)
    settings.comfyui_output_dir.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    image_name = f"{input_path.stem}.png"
    comfy_input = settings.comfyui_input_dir / image_name
    shutil.copy2(input_path, comfy_input)
    logger.info("polish copied input → %s", comfy_input)

    workflow = _patch_workflow(
        _load_workflow(settings.workflow_polish_path),
        image_name=image_name,
        settings=settings,
        denoise=denoise,
        seed=seed,
    )
    prompt_id = _submit_prompt(settings.comfyui_url, workflow)
    logger.info("polish submitted prompt_id=%s denoise=%s", prompt_id, denoise)

    history = _wait_history(
        settings.comfyui_url, prompt_id, settings.comfyui_timeout_sec
    )
    src = _output_image_path(history, settings.comfyui_output_dir)
    shutil.copy2(src, output_path)
    logger.info("polish wrote %s", output_path)
