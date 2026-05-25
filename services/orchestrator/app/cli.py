import argparse
import logging
import sys
from pathlib import Path

from app.config import get_settings
from app.pipeline import upscale
from app.pipeline.errors import PipelineError
from app.pipeline.runner import PipelineOptions, run_pipeline, run_rembg_stage

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Full pipeline (rembg → upscale → optional polish)")
    run_p.add_argument("--input", type=Path, required=True)
    run_p.add_argument(
        "--mode",
        type=str,
        default=None,
        choices=("full", "deterministic"),
        help="Override PIPELINE_MODE",
    )
    run_p.add_argument("--denoise", type=float, default=None)
    run_p.add_argument("--seed", type=int, default=None)
    run_p.add_argument("--model", type=str, default=None, help="Override REMBG_MODEL")

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

    if args.command == "run":
        try:
            result = run_pipeline(
                args.input,
                settings,
                PipelineOptions(
                    mode=args.mode or settings.pipeline_mode,
                    denoise=args.denoise
                    if args.denoise is not None
                    else settings.pipeline_denoise,
                    seed=args.seed if args.seed is not None else settings.sd_seed,
                    rembg_model=args.model,
                ),
            )
        except PipelineError as e:
            logger.error("pipeline failed at %s: %s", e.failed_stage, e)
            if e.artifacts:
                logger.error("artifacts: %s", e.artifacts)
            return 1
        logger.info(
            "pipeline done → %s (%d ms) artifacts=%s",
            result.output_path,
            result.duration_ms,
            result.artifacts,
        )
        return 0

    if args.command == "stage" and args.stage_name == "rembg":
        model = args.model or settings.rembg_model
        run_rembg_stage(
            args.input,
            args.output,
            model=model,
            model_dir=settings.rembg_model_dir,
        )
        logger.info("stage rembg done → %s", args.output)
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
