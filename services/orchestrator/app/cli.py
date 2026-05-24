import argparse
import logging
import sys
import tempfile
from pathlib import Path

from app.config import get_settings
from app.pipeline import composite, remove_bg, upscale

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _run_rembg_stage(input_path: Path, output_path: Path, *, model: str, model_dir: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        cutout = Path(tmp) / "cutout.png"
        remove_bg.run(input_path, cutout, model=model, model_dir=model_dir)
        composite.run(cutout, output_path)
    logger.info("stage rembg done → %s", output_path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="command", required=True)

    stage = sub.add_parser("stage", help="Run a single pipeline stage")
    stage_sub = stage.add_subparsers(dest="stage_name", required=True)

    rembg_p = stage_sub.add_parser("rembg", help="Background removal + white composite")
    rembg_p.add_argument("--input", type=Path, required=True)
    rembg_p.add_argument("--output", type=Path, required=True)
    rembg_p.add_argument("--model", type=str, default=None, help="Override REMBG_MODEL")

    upscale_p = stage_sub.add_parser("upscale", help="Real-ESRGAN 2x upscale")
    upscale_p.add_argument("--input", type=Path, required=True)
    upscale_p.add_argument("--output", type=Path, required=True)
    upscale_p.add_argument("--scale", type=int, default=None, help="Override PIPELINE_UPSCALE")

    args = parser.parse_args(argv)
    settings = get_settings()

    if args.command == "stage" and args.stage_name == "rembg":
        model = args.model or settings.rembg_model
        _run_rembg_stage(
            args.input,
            args.output,
            model=model,
            model_dir=settings.rembg_model_dir,
        )
        return 0

    if args.command == "stage" and args.stage_name == "upscale":
        scale = args.scale if args.scale is not None else settings.pipeline_upscale
        upscale.run(
            args.input,
            args.output,
            scale=scale,
            weights_path=settings.realesrgan_weights_path,
        )
        logger.info("stage upscale done → %s", args.output)
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
