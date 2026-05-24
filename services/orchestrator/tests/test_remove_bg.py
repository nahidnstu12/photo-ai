import io
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from app.pipeline.errors import StageError
from app.pipeline.remove_bg import run


def test_remove_bg_empty_alpha_raises(tmp_path: Path) -> None:
    inp = tmp_path / "in.jpg"
    out = tmp_path / "out.png"
    inp.write_bytes(b"fake")

    empty = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    buf = io.BytesIO()
    empty.save(buf, format="PNG")

    mock_session = MagicMock()
    with (
        patch("rembg.new_session", return_value=mock_session),
        patch("rembg.remove", return_value=buf.getvalue()),
    ):
        with pytest.raises(StageError, match="Cutout is empty"):
            run(inp, out, model="u2net_cloth_seg")
