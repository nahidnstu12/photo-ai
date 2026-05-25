import logging
from pathlib import Path

import cv2

from app.pipeline.errors import StageError

logger = logging.getLogger(__name__)


def _validate_weights(weights_path: Path) -> None:
    if not weights_path.is_file():
        raise StageError(
            f"Real-ESRGAN weights not found: {weights_path}. "
            "See README model downloads."
        )
    size = weights_path.stat().st_size
    if size < 1_000_000:
        head = weights_path.read_bytes()[:32]
        raise StageError(
            f"Invalid Real-ESRGAN weights ({size} bytes at {weights_path}). "
            "Re-download: curl -fL -o data/models/realesrgan/RealESRGAN_x4plus.pth "
            "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth "
            f"(file starts with: {head[:20]!r})"
        )


def _build_upsampler(weights_path: Path, tile: int) -> object:
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
    return RealESRGANer(
        scale=4,
        model_path=str(weights_path),
        model=model,
        tile=tile,
        tile_pad=10,
        pre_pad=0,
        half=False,
    )


def _tile_for_image(h: int, w: int) -> int:
    # 0 = no tiling; 256 = lower peak RAM for large images in Docker
    if h * w <= 1_500_000:
        return 0
    return 256


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

    _validate_weights(weights_path)
    h, w = img.shape[:2]
    tile = _tile_for_image(h, w)
    logger.info("upscale %s → %s (%dx, tile=%s)", input_path, output_path, scale, tile)
    upsampler = _build_upsampler(weights_path, tile)
    output, _ = upsampler.enhance(img, outscale=scale)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(output_path), output):
        raise StageError(f"Failed to write: {output_path}")
    logger.info("upscale wrote %s (%dx%d)", output_path, output.shape[1], output.shape[0])
