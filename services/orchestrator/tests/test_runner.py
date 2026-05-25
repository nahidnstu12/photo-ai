from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image

from app.config import Settings
from app.pipeline.errors import PipelineError
from app.pipeline.runner import PipelineOptions, png_to_jpg, run_pipeline


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        DATA_DIR=str(tmp_path),
        PIPELINE_MODE="deterministic",
        PIPELINE_UPSCALE=2,
    )


def _write_rgb(path: Path, size: tuple[int, int] = (64, 80)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color=(200, 50, 50)).save(path, "JPEG")


@pytest.mark.parametrize("mode", ["deterministic", "full"])
def test_run_pipeline_writes_output(tmp_path: Path, mode: str) -> None:
    settings = _settings(tmp_path)
    settings.ensure_data_dirs()
    inp = settings.input_dir / "sample.jpg"
    _write_rgb(inp)

    with (
        patch("app.pipeline.runner.run_rembg_stage") as rembg,
        patch("app.pipeline.runner.upscale.run") as up,
        patch("app.pipeline.runner.polish.run") as pol,
    ):
        def fake_rembg(i: Path, o: Path, **kw: object) -> None:
            Image.new("RGBA", (64, 80), (255, 0, 0, 255)).save(o, "PNG")

        def fake_up(i: Path, o: Path, **kw: object) -> None:
            Image.new("RGB", (128, 160), (0, 255, 0)).save(o, "PNG")

        def fake_pol(i: Path, o: Path, **kw: object) -> None:
            Image.new("RGB", (128, 160), (0, 0, 255)).save(o, "PNG")

        rembg.side_effect = fake_rembg
        up.side_effect = fake_up
        pol.side_effect = fake_pol

        result = run_pipeline(
            inp,
            settings,
            PipelineOptions(mode=mode, denoise=0.25, seed=42),
        )

    assert result.output_path == settings.output_dir / "sample.jpg"
    assert result.output_path.is_file()
    assert "stage1_nobg" in result.artifacts
    assert "stage2_upscale" in result.artifacts
    if mode == "full":
        pol.assert_called_once()
        assert "stage3_sd" in result.artifacts
    else:
        pol.assert_not_called()
        assert "stage3_sd" not in result.artifacts


def test_pipeline_error_keeps_artifacts(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    settings.ensure_data_dirs()
    inp = settings.input_dir / "fail.jpg"
    _write_rgb(inp)

    with patch("app.pipeline.runner.run_rembg_stage") as rembg:
        rembg.side_effect = lambda *a, **k: Image.new("RGBA", (10, 10)).save(
            settings.stage1_nobg_dir / "fail.png", "PNG"
        )

        with patch(
            "app.pipeline.runner.upscale.run",
            side_effect=Exception("upscale boom"),
        ):
            with pytest.raises(PipelineError) as exc:
                run_pipeline(inp, settings, PipelineOptions(mode="deterministic"))

    assert exc.value.failed_stage == "upscale"
    assert "stage1_nobg" in exc.value.artifacts


def test_png_to_jpg(tmp_path: Path) -> None:
    src = tmp_path / "a.png"
    dst = tmp_path / "a.jpg"
    Image.new("RGBA", (32, 32), (255, 128, 0, 200)).save(src, "PNG")
    png_to_jpg(src, dst, quality=92)
    assert dst.is_file()
    with Image.open(dst) as im:
        assert im.format == "JPEG"
        assert im.mode == "RGB"
