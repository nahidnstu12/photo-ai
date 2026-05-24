from pathlib import Path

from PIL import Image

from app.pipeline.composite import run


def test_composite_on_white(tmp_path: Path) -> None:
    rgba = tmp_path / "cutout.png"
    out = tmp_path / "out.png"

    img = Image.new("RGBA", (20, 20), (200, 50, 50, 255))
    img.putalpha(Image.new("L", (20, 20), 0))
    # opaque red square in center
    for x in range(6, 14):
        for y in range(6, 14):
            img.putpixel((x, y), (200, 50, 50, 255))

    img.save(rgba)
    run(rgba, out)

    result = Image.open(out).convert("RGB")
    assert result.size == (20, 20)
    # center pixel stays reddish
    assert result.getpixel((10, 10))[0] > 150
    # corner should be white
    assert result.getpixel((0, 0)) == (255, 255, 255)
