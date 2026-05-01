from __future__ import annotations

from typing import Any

from docs_config import PROJECT_DESCRIPTION
from docs_weeklies import readme_week_label
from paperlib import ROOT, compact_paper_item, load_yaml, write_text


def build_readme(weeklies: list[dict[str, Any]], paper_index: dict[str, Any]) -> None:
    lines = [
        '<p align="center">',
        '  <img src="docs/assets/title.svg" alt="Enzyme AI Papers" width="760">',
        "</p>",
        "",
        PROJECT_DESCRIPTION,
        "URL-first, curator-reviewed, and designed for quick reading.",
        newsletter_intro_line(),
        "",
    ]

    latest = weeklies[0] if weeklies else None
    if latest is None:
        lines.extend(["## This Week", "", "No weekly digest has been published yet.", ""])
    else:
        append_readme_week(lines, latest, paper_index, readme_week_label(latest, 0))
        if len(weeklies) > 1:
            append_readme_week(lines, weeklies[1], paper_index, readme_week_label(weeklies[1], 1))

    lines.extend(
        [
            "## Usage",
            "",
            "- Quick workflow guide for issue and Actions workflows: [USE_GUIDELINE.md](USE_GUIDELINE.md)",
            "- Guide for readers, submitters, and group maintainers: [MORE_INFO.md](MORE_INFO.md)",
            "- Submit a paper by opening a GitHub issue with a paper URL; notes, tags, and code links are optional.",
            "- Maintainers review issue previews and apply `accepted`, `needs-info`, or `rejected`.",
            "- Accepted papers are generated through pull requests; the README and website are rebuilt from `data/papers/`.",
            "",
        ]
    )

    write_text(ROOT / "README.md", "\n".join(lines).rstrip() + "\n")


def newsletter_intro_line() -> str:
    url = newsletter_subscribe_url()
    if not url:
        return ""
    return f"Weekly email: [subscribe to the digest]({url})."


def newsletter_subscribe_url() -> str:
    config = load_yaml(ROOT / "mkdocs.yml")
    if not isinstance(config, dict):
        return ""
    extra = config.get("extra")
    if not isinstance(extra, dict):
        return ""
    newsletter = extra.get("newsletter")
    if not isinstance(newsletter, dict):
        return ""
    subscribe_url = str(newsletter.get("subscribe_url") or "").strip()
    if subscribe_url:
        return subscribe_url
    username = str(newsletter.get("buttondown_username") or "").strip()
    return f"https://buttondown.com/{username}" if username else ""


def append_readme_week(
    lines: list[str],
    weekly: dict[str, Any],
    paper_index: dict[str, Any],
    label: str,
) -> None:
    lines.extend(
        [
            f"## {label}: {weekly['title']} ({weekly['date_range']})",
            "",
            weekly["summary"],
            "",
            "### Papers",
            "",
        ]
    )

    for paper_id in weekly["paper_ids"]:
        lines.append(compact_paper_item(paper_index[paper_id]))
        lines.append("")
