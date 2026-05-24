from pathlib import Path

from PIL import Image


def run(input_path: Path, output_path: Path) -> None:
    """RGBA cutout → RGB on white (255, 255, 255)."""
    img = Image.open(input_path).convert("RGBA")
    white = Image.new("RGBA", img.size, (255, 255, 255, 255))
    final = Image.alpha_composite(white, img).convert("RGB")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    final.save(output_path, "PNG")
