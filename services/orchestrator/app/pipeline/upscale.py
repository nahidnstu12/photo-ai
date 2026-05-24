import logging
from pathlib import Path

import cv2

from app.pipeline.errors import StageError

logger = logging.getLogger(__name__)

_upsampler = None


def _get_upsampler(weights_path: Path):
    global _upsampler
    if _upsampler is not None:
        return _upsampler

    if not weights_path.is_file():
        raise StageError(
            f"Real-ESRGAN weights not found: {weights_path}. "
            "Run ./scripts/download-models.sh on the host."
        )

    from basicsr.archs.rrdbnet_arch import RRDBNet
    from realesrgan import RealESRGANer

    model = RRDBNet(
        num_in_ch=3,
        num_out_ch=3,
        num_feat=64,
        num_block=23,
        num_grow_ch=32,
        scale=4,
    )
    _upsampler = RealESRGANer(
        scale=4,
        model_path=str(weights_path),
        model=model,
        tile=400,
        tile_pad=10,
        pre_pad=0,
        half=False,
    )
    logger.info("Real-ESRGAN loaded from %s", weights_path)
    return _upsampler


def run(
    input_path: Path,
    output_path: Path,
    *,
    scale: int = 2,
    weights_path: Path,
) -> None:
    if not input_path.is_file():
        raise StageError(f"Input not found: {input_path}")
    if scale != 2:
        raise StageError("Only 2x upscale is supported (set PIPELINE_UPSCALE=2).")

    img = cv2.imread(str(input_path), cv2.IMREAD_COLOR)
    if img is None:
        raise StageError(f"Could not read image: {input_path}")

    upsampler = _get_upsampler(weights_path)
    logger.info("upscale %s → %s (%dx)", input_path, output_path, scale)
    output, _ = upsampler.enhance(img, outscale=scale)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(output_path), output):
        raise StageError(f"Failed to write: {output_path}")
    logger.info("upscale wrote %s (%dx%d)", output_path, output.shape[1], output.shape[0])
