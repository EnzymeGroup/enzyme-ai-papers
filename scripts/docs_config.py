from __future__ import annotations

from paperlib import ROOT


PROJECT_DESCRIPTION = (
    "A curated weekly digest of AI and computational papers for enzyme design, "
    "engineering, function prediction, and biocatalysis."
)
DOCS_SOURCE_DIR = ROOT / "docs_src"
GENERATED = "<!-- AUTO-GENERATED. DO NOT EDIT DIRECTLY. -->\n\n"
PAGE_PREFIX = "---\nhide:\n  - navigation\n  - toc\n---\n\n" + GENERATED
