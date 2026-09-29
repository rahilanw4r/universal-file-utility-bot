from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

FORMAT_MAP = {
    ".png": "PNG",
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".webp": "WEBP",
}


def convert_image(source: Path, target: Path, output_format: str) -> None:
    output_format = output_format.lower().lstrip(".")
    ext = ".jpg" if output_format == "jpg" else f".{output_format}"
    if ext not in FORMAT_MAP:
        raise ValueError("Unsupported image format.")

    # Pillow's decompression-bomb protection remains enabled by default.
    with Image.open(source) as opened:
        opened.verify()
    with Image.open(source) as opened:
        image = ImageOps.exif_transpose(opened)
        image.load()
        fmt = FORMAT_MAP[ext]
        if fmt == "JPEG":
            if image.mode in ("RGBA", "LA") or "transparency" in image.info:
                rgba = image.convert("RGBA")
                background = Image.new("RGB", rgba.size, "white")
                background.paste(rgba, mask=rgba.getchannel("A"))
                image = background
            else:
                image = image.convert("RGB")
            image.save(target, format=fmt, quality=90, optimize=True)
        elif fmt == "PNG":
            image.convert("RGBA" if "A" in image.getbands() else "RGB").save(target, format=fmt, optimize=True)
        else:
            image.convert("RGBA" if "A" in image.getbands() else "RGB").save(target, format=fmt, quality=90, method=4)
