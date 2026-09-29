from __future__ import annotations

import zipfile
from pathlib import Path


def create_zip(sources: list[Path], target: Path) -> None:
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source in sources:
            archive.write(source, arcname=source.name)
