from pathlib import Path
from PIL import Image


def create_snapshot(image_path: Path, output_path: Path, max_size=(360, 360)) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.open(image_path).convert("RGB")
    image.thumbnail(max_size)
    image.save(output_path, format="JPEG", quality=85)
