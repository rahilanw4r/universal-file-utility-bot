from __future__ import annotations

from pathlib import Path

from PIL import Image
from pypdf import PdfWriter, PdfReader


def merge_pdfs(sources: list[Path], target: Path) -> None:
    writer = PdfWriter()

    for source in sources:
        reader = PdfReader(str(source))
        for page in reader.pages:
            writer.add_page(page)

    with target.open("wb") as handle:
        writer.write(handle)


def images_to_pdf(sources: list[Path], target: Path) -> None:
    images = []

    try:
        for source in sources:
            image = Image.open(source).convert("RGB")
            images.append(image)

        if not images:
            raise ValueError("No images supplied.")

        first, *rest = images
        first.save(target, "PDF", save_all=True, append_images=rest)
    finally:
        for image in images:
            image.close()
