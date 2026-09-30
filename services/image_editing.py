from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter, ImageOps


def edit_image(source: Path, target: Path, action: str, width: int = 0, height: int = 0) -> None:
    with Image.open(source) as opened:
        image = ImageOps.exif_transpose(opened).copy()
    try:
        if action == "resize":
            if not (1 <= width <= 10000 and 1 <= height <= 10000):
                raise ValueError("Width and height must each be between 1 and 10000 pixels.")
            resized = image.resize((width, height), Image.Resampling.LANCZOS)
            image.close()
            image = resized
        elif action == "rotate": image = image.rotate(90, expand=True)
        elif action == "flip": image = ImageOps.mirror(image)
        elif action == "flop": image = ImageOps.flip(image)
        elif action == "gray": image = ImageOps.grayscale(image)
        elif action == "invert":
            if image.mode == "RGBA":
                a = image.getchannel("A")
                image = ImageOps.invert(image.convert("RGB")).convert("RGBA")
                image.putalpha(a)
            else: image = ImageOps.invert(image.convert("RGB"))
        elif action == "autocontrast": image = ImageOps.autocontrast(image.convert("RGB"))
        elif action == "blur": image = image.filter(ImageFilter.GaussianBlur(radius=2))
        elif action == "sharpen": image = image.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
        elif action == "bright": image = ImageEnhance.Brightness(image).enhance(1.25)
        elif action == "dark": image = ImageEnhance.Brightness(image).enhance(0.75)
        elif action == "contrast": image = ImageEnhance.Contrast(image).enhance(1.35)
        elif action == "saturate": image = ImageEnhance.Color(image).enhance(1.5)
        elif action == "sepia":
            rgb = image.convert("RGB")
            gray = ImageOps.grayscale(rgb)
            rgb.close()
            image = ImageOps.colorize(gray, "#704214", "#fff1d0")
            gray.close()
        else: raise ValueError("Unknown edit action.")
        if image.mode not in ("RGB", "RGBA", "L"):
            image = image.convert("RGBA" if "transparency" in image.info else "RGB")
        image.save(target, format="PNG", optimize=True)
    finally:
        image.close()


def remove_background(source: Path, target: Path) -> None:
    """Optional free local AI background removal; requires the rembg extra."""
    try:
        from rembg import remove
    except ImportError as exc:
        raise RuntimeError("Background removal is not installed on this server. Install requirements-ai.txt and redeploy.") from exc
    with Image.open(source) as opened:
        result = remove(opened.convert("RGBA"))
        result.save(target, format="PNG")
