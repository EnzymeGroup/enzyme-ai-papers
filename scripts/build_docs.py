from __future__ import annotations

import shutil
import sys

from docs_assets import copy_assets
from docs_readme import build_readme
from docs_site import build_archive_page, build_home_page, build_info_page, build_subscribe_page
from docs_weeklies import derive_weeklies
from paperlib import DOCS_DIR, index_papers, load_papers, sorted_papers, validate_all


def main() -> int:
    errors = validate_all()
    if errors:
        print("Cannot build MkDocs pages because validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    papers = sorted_papers(load_papers())
    paper_index = index_papers(papers)
    weeklies = derive_weeklies(papers)
    latest = weeklies[0] if weeklies else None

    build_readme(weeklies, paper_index)
    clean_docs_dir()
    build_home_page(latest, paper_index)
    build_archive_page(papers, paper_index, weeklies, latest)
    build_subscribe_page(latest)
    build_info_page(latest)
    copy_assets()

    print("MkDocs pages and README generated.")
    return 0


def clean_docs_dir() -> None:
    shutil.rmtree(DOCS_DIR, ignore_errors=True)
    (DOCS_DIR / "assets").mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    sys.exit(main())
