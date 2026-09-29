from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps

FORMAT_MAP = {".png": "PNG", ".jpg": "JPEG", ".jpeg": "JPEG", ".webp": "WEBP"}


def _load_rgb(source: Path) -> Image.Image:
    with Image.open(source) as opened:
        opened.verify()
    with Image.open(source) as opened:
        image = ImageOps.exif_transpose(opened)
        image.load()
        if image.mode in ("RGBA", "LA") or "transparency" in image.info:
            rgba = image.convert("RGBA")
            background = Image.new("RGB", rgba.size, "white")
            background.paste(rgba, mask=rgba.getchannel("A"))
            rgba.close()
            return background
        return image.convert("RGB")


def convert_image(source: Path, target: Path, output_format: str) -> None:
    output_format = output_format.lower().lstrip(".")
    ext = ".jpg" if output_format == "jpg" else f".{output_format}"
    if ext not in FORMAT_MAP:
        raise ValueError("Unsupported image format.")
    with _load_rgb(source) as image:
        fmt = FORMAT_MAP[ext]
        options = {"quality": 90, "optimize": True} if fmt == "JPEG" else {}
        if fmt == "WEBP":
            options = {"quality": 90, "method": 4}
        image.save(target, format=fmt, **options)


def compress_to_target(source: Path, target: Path, target_bytes: int) -> int:
    """Keep dimensions where possible; reduce quality first, then dimensions if needed."""
    if target_bytes < 10_000:
        raise ValueError("Choose a target size of at least 10 KB.")
    image = _load_rgb(source)
    current = image
    try:
        while True:
            best = None
            low, high = 20, 95
            while low <= high:
                quality = (low + high) // 2
                buffer = BytesIO()
                current.save(buffer, format="JPEG", quality=quality, optimize=True)
                encoded = buffer.getvalue()
                if len(encoded) <= target_bytes:
                    best = encoded
                    low = quality + 1
                else:
                    high = quality - 1
            if best is not None:
                target.write_bytes(best)
                return len(best)
            if min(current.size) <= 320:
                buffer = BytesIO()
                current.save(buffer, format="JPEG", quality=20, optimize=True)
                target.write_bytes(buffer.getvalue())
                return target.stat().st_size
            resized = current.resize(
                (max(1, int(current.width * 0.8)), max(1, int(current.height * 0.8))),
                Image.Resampling.LANCZOS,
            )
            if current is not image:
                current.close()
            current = resized
    finally:
        if current is not image:
            current.close()
        image.close()
