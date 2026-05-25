import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.config import Settings
from app.pipeline.errors import StageError
from app.pipeline.polish import _patch_workflow, _resolve_seed, run


def test_resolve_seed_random() -> None:
    assert _resolve_seed(-1) >= 0


def test_patch_workflow(tmp_path: Path) -> None:
    wf_path = tmp_path / "wf.json"
    wf_path.write_text(
        json.dumps(
            {
                "1": {"inputs": {"image": "input.png"}},
                "2": {"inputs": {"ckpt_name": "old.safetensors"}},
                "6": {"inputs": {"denoise": 0.3, "seed": 0, "steps": 20, "cfg": 7, "sampler_name": "x"}},
            }
        ),
        encoding="utf-8",
    )
    settings = Settings(
        DATA_DIR=str(tmp_path),
        WORKFLOW_POLISH_PATH=str(wf_path),
        SD_CHECKPOINT="ckpt.safetensors",
        SD_STEPS=15,
        SD_CFG=6.5,
        SD_SAMPLER="euler",
    )
    wf = {"1": {"inputs": {}}, "2": {"inputs": {}}, "6": {"inputs": {}}}
    patched = _patch_workflow(
        wf, image_name="shirt.png", settings=settings, denoise=0.25, seed=99
    )
    assert patched["1"]["inputs"]["image"] == "shirt.png"
    assert patched["2"]["inputs"]["ckpt_name"] == "ckpt.safetensors"
    assert patched["6"]["inputs"]["denoise"] == 0.25
    assert patched["6"]["inputs"]["seed"] == 99
    assert patched["6"]["inputs"]["steps"] == 15


def test_run_polish_copies_output(tmp_path: Path) -> None:
    settings = Settings(DATA_DIR=str(tmp_path))
    settings.ensure_data_dirs()
    inp = tmp_path / "in.png"
    out = settings.stage3_sd_dir / "in.png"

    history = {
        "outputs": {
            "8": {"images": [{"filename": "photo_ai_polish_00001_.png", "subfolder": ""}]}
        }
    }
    comfy_out = settings.comfyui_output_dir / "photo_ai_polish_00001_.png"
    comfy_out.parent.mkdir(parents=True, exist_ok=True)
    from PIL import Image

    Image.new("RGB", (4, 4)).save(comfy_out, "PNG")

    with (
        patch("app.pipeline.polish._submit_prompt", return_value="pid-1"),
        patch("app.pipeline.polish._wait_history", return_value=history),
        patch("app.pipeline.polish._load_workflow", return_value={"1": {"inputs": {}}, "2": {"inputs": {}}, "6": {"inputs": {}}}),
        patch("app.pipeline.polish._patch_workflow", return_value={}),
    ):
        # valid png for copy2 source
        Image.new("RGB", (8, 8)).save(inp, "PNG")
        run(inp, out, settings=settings, denoise=0.3, seed=1)

    assert out.is_file()


def test_submit_prompt_node_errors(tmp_path: Path) -> None:
    from app.pipeline import polish as polish_mod

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"node_errors": {"6": "bad sampler"}}

    with patch.object(httpx.Client, "post", return_value=mock_resp):
        with pytest.raises(StageError, match="node errors"):
            polish_mod._submit_prompt("http://comfyui:8188", {})
