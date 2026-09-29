from __future__ import annotations

from pathlib import Path

from PIL import Image


FORMAT_MAP = {
    ".png": ("PNG", "RGBA"),
    ".jpg": ("JPEG", "RGB"),
    ".jpeg": ("JPEG", "RGB"),
    ".webp": ("WEBP", "RGBA"),
}


def convert_image(source: Path, target: Path, output_format: str) -> None:
    output_format = output_format.lower().lstrip(".")
    ext = f".{output_format}"

    if ext not in FORMAT_MAP:
        raise ValueError("Unsupported image format.")

    pil_format, mode = FORMAT_MAP[ext]

    with Image.open(source) as image:
        if pil_format == "JPEG":
            if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
                background = Image.new("RGB", image.size, "white")
                rgba = image.convert("RGBA")
                background.paste(rgba, mask=rgba.getchannel("A"))
                image = background
            else:
                image = image.convert("RGB")
        elif mode == "RGBA":
            image = image.convert("RGBA")

        image.save(target, format=pil_format, quality=92 if pil_format == "JPEG" else None)
