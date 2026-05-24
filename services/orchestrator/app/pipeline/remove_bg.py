import io
import logging
import os
from pathlib import Path

from PIL import Image

from app.pipeline.errors import StageError

logger = logging.getLogger(__name__)


def _has_foreground(img: Image.Image) -> bool:
    _min, max_alpha = img.getchannel("A").getextrema()
    return max_alpha > 16


def run(
    input_path: Path,
    output_path: Path,
    *,
    model: str = "u2net_cloth_seg",
    model_dir: Path | None = None,
) -> None:
    """Remove background; write RGBA PNG."""
    if model_dir is not None:
        model_dir.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("U2NET_HOME", str(model_dir))

    if not input_path.is_file():
        raise StageError(f"Input not found: {input_path}")

    from rembg import new_session, remove

    logger.info("rembg model=%s input=%s (first run may download ~170MB)", model, input_path)
    session = new_session(model)
    result = remove(input_path.read_bytes(), session=session)
    img = Image.open(io.BytesIO(result)).convert("RGBA")

    if not _has_foreground(img):
        raise StageError(
            "Cutout is empty — subject may be missing or same color as background. "
            "Try a clearer photo or different REMBG_MODEL."
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG")
    logger.info("rembg wrote %s", output_path)
