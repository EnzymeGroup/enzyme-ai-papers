from __future__ import annotations

import shutil

from docs_config import DOCS_SOURCE_DIR
from paperlib import DOCS_DIR, ProjectError


ASSET_FILES = ("title.svg", "site.css", "app.js")


def copy_assets() -> None:
    source_dir = DOCS_SOURCE_DIR / "assets"
    target_dir = DOCS_DIR / "assets"
    target_dir.mkdir(parents=True, exist_ok=True)

    for filename in ASSET_FILES:
        source = source_dir / filename
        if not source.exists():
            raise ProjectError(f"missing docs source asset: {source}")
        shutil.copy2(source, target_dir / filename)
