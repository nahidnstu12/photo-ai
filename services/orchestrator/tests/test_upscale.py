from pathlib import Path
from unittest.mock import MagicMock, patch

import cv2
import pytest
from PIL import Image

from app.pipeline.errors import StageError
from app.pipeline.upscale import run


def test_upscale_missing_weights(tmp_path: Path) -> None:
    inp = tmp_path / "in.png"
    out = tmp_path / "out.png"
    Image.new("RGB", (10, 10), (128, 128, 128)).save(inp)

    with pytest.raises(StageError, match="weights not found"):
        run(inp, out, scale=2, weights_path=tmp_path / "missing.pth")


def test_upscale_doubles_dimensions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    inp = tmp_path / "in.png"
    out = tmp_path / "out.png"
    weights = tmp_path / "fake.pth"
    weights.touch()

    Image.new("RGB", (50, 40), (100, 100, 100)).save(inp)
    img = cv2.imread(str(inp))

    mock_upsampler = MagicMock()
    mock_upsampler.enhance.return_value = (
        cv2.resize(img, (100, 80), interpolation=cv2.INTER_LINEAR),
        None,
    )

    with patch("app.pipeline.upscale._get_upsampler", return_value=mock_upsampler):
        run(inp, out, scale=2, weights_path=weights)

    result = Image.open(out)
    assert result.size == (100, 80)
