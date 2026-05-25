import logging
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from app.config import Settings
from app.pipeline import composite, polish, remove_bg, upscale
from app.pipeline.errors import PipelineError, StageError

logger = logging.getLogger(__name__)

JPEG_QUALITY = 92


@dataclass(frozen=True)
class PipelineOptions:
    mode: str = "full"
    denoise: float = 0.30
    seed: int = -1
    rembg_model: str | None = None


@dataclass(frozen=True)
class PipelineResult:
    output_path: Path
    artifacts: dict[str, str]
    duration_ms: int


def run_rembg_stage(
    input_path: Path,
    output_path: Path,
    *,
    model: str,
    model_dir: Path,
) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        cutout = Path(tmp) / "cutout.png"
        remove_bg.run(input_path, cutout, model=model, model_dir=model_dir)
        composite.run(cutout, output_path)
    logger.info("rembg+composite → %s", output_path)


def png_to_jpg(src: Path, dst: Path, *, quality: int = JPEG_QUALITY) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        rgb = im.convert("RGB") if im.mode != "RGB" else im
        rgb.save(dst, "JPEG", quality=quality, optimize=True)
    logger.info("final jpg → %s", dst)


def run_pipeline(
    input_path: Path,
    settings: Settings,
    options: PipelineOptions,
) -> PipelineResult:
    if not input_path.is_file():
        raise PipelineError(f"Input not found: {input_path}", failed_stage="input")

    mode = options.mode.strip().lower()
    if mode not in ("full", "deterministic"):
        raise PipelineError(
            f"Invalid pipeline_mode: {options.mode!r}",
            failed_stage="config",
        )

    stem = input_path.stem
    model = options.rembg_model or settings.rembg_model
    artifacts: dict[str, Path] = {}
    stage = "rembg"
    t0 = time.perf_counter()

    try:
        stage1 = settings.stage1_nobg_dir / f"{stem}.png"
        run_rembg_stage(
            input_path,
            stage1,
            model=model,
            model_dir=settings.rembg_model_dir,
        )
        artifacts["stage1_nobg"] = stage1

        stage = "upscale"
        stage2 = settings.stage2_upscale_dir / f"{stem}.png"
        upscale.run(
            input_path=stage1,
            output_path=stage2,
            scale=settings.pipeline_upscale,
            weights_path=settings.realesrgan_weights_path,
        )
        artifacts["stage2_upscale"] = stage2

        output_jpg = settings.output_dir / f"{stem}.jpg"

        if mode == "full":
            stage = "polish"
            stage3 = settings.stage3_sd_dir / f"{stem}.png"
            polish.run(
                stage2,
                stage3,
                settings=settings,
                denoise=options.denoise,
                seed=options.seed,
            )
            artifacts["stage3_sd"] = stage3
            png_to_jpg(stage3, output_jpg)
        else:
            png_to_jpg(stage2, output_jpg)

        duration_ms = int((time.perf_counter() - t0) * 1000)
        return PipelineResult(
            output_path=output_jpg,
            artifacts={k: str(v) for k, v in artifacts.items()},
            duration_ms=duration_ms,
        )
    except StageError as e:
        raise PipelineError(
            str(e),
            failed_stage=stage,
            artifacts={k: str(v) for k, v in artifacts.items()},
        ) from e
    except Exception as e:
        raise PipelineError(
            str(e),
            failed_stage=stage,
            artifacts={k: str(v) for k, v in artifacts.items()},
        ) from e
