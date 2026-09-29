from __future__ import annotations

import shutil
from pathlib import Path


def safe_suffix(name: str, default: str = ".bin") -> str:
    suffix = Path(name).suffix.lower()
    return suffix if suffix and len(suffix) <= 10 else default


def remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    elif path.exists():
        try:
            path.unlink()
        except OSError:
            pass
