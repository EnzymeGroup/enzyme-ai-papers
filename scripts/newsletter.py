from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import yaml

from docs_weeklies import derive_weeklies
from paperlib import (
    MAILINGS_DIR,
    ROOT,
    ProjectError,
    display_note,
    display_summary,
    format_links,
    format_tags,
    index_papers,
    load_papers,
    load_yaml,
    project_now,
    sorted_papers,
    write_text,
)


DELIVERED_STATUSES = {"about_to_send", "in_flight", "scheduled", "sent"}


@dataclass(frozen=True)
class NewsletterIssue:
    week: str
    title: str
    date_range: str
    summary: str
    subject: str
    body: str
    paper_ids: list[str]
    content_sha256: str
    archive_url: str

    @property
    def slug(self) -> str:
        return f"enzyme-ai-papers-{self.week.lower()}"


def previous_iso_week(reference: date | None = None) -> str:
    value = reference or project_now().date()
    previous_week_day = value - timedelta(days=7)
    year, week, _weekday = previous_week_day.isocalendar()
    return f"{year}-W{week:02d}"


def build_newsletter_issue(week: str | None = None) -> NewsletterIssue | None:
    target_week = week or previous_iso_week()
    papers = sorted_papers(load_papers())
    paper_index = index_papers(papers)
    weekly = weekly_by_id(derive_weeklies(papers)).get(target_week)
    if weekly is None:
        return None

    subject = str(weekly["title"])
    archive_url = weekly_archive_url(target_week)
    body = render_newsletter_body(weekly, paper_index, archive_url)
    digest = hashlib.sha256(f"{subject}\n{body}".encode("utf-8")).hexdigest()
    return NewsletterIssue(
        week=target_week,
        title=str(weekly["title"]),
        date_range=str(weekly["date_range"]),
        summary=str(weekly["summary"]),
        subject=subject,
        body=body,
        paper_ids=[str(paper_id) for paper_id in weekly["paper_ids"]],
        content_sha256=digest,
        archive_url=archive_url,
    )


def weekly_by_id(weeklies: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(weekly["week"]): weekly for weekly in weeklies}


def render_newsletter_body(weekly: dict[str, Any], paper_index: dict[str, Any], archive_url: str) -> str:
    commentary = weekly.get("commentary", {})
    lines = [
        "<!-- buttondown-editor-mode: fancy -->",
        "",
        f"# {weekly['title']}",
        "",
        f"**{weekly['week']}** - {weekly['date_range']}",
        "",
        str(weekly["summary"]),
        "",
    ]
    if archive_url:
        lines.extend([f"[Read this issue on the website]({archive_url})", ""])

    lines.extend(["## Papers", ""])
    for paper_id in weekly["paper_ids"]:
        commentary_note = commentary.get(paper_id) if isinstance(commentary, dict) else None
        lines.extend(render_newsletter_paper(paper_index[paper_id], commentary_note))

    lines.extend(
        [
            "---",
            "",
            "You are receiving this because you subscribed to Enzyme AI Papers.",
            "Subscriber addresses and unsubscribe preferences are managed by the newsletter provider, not this repository.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_newsletter_paper(record: Any, commentary: str | None = None) -> list[str]:
    paper = record.data
    authors = ", ".join(str(author) for author in paper.get("authors", []))
    summary = display_summary(paper)
    note = display_note(paper, commentary)
    tags = format_tags(paper)
    links = format_links(paper)

    lines = [f"### {paper['title']}", ""]
    if authors:
        lines.extend([f"**Authors:** {authors}", ""])
    lines.extend([f"**Source / Year:** {paper['source']}, {paper['year']}", ""])
    if summary:
        lines.extend([f"**Summary:** {summary}", ""])
    if note:
        lines.extend([f"**Note:** {note}", ""])
    if tags:
        lines.extend([f"**Tags:** {tags}", ""])
    if links:
        lines.extend([f"**Links:** {links}", ""])
    return lines


def weekly_archive_url(week: str) -> str:
    site_url = project_site_url()
    if not site_url:
        return ""
    return f"{site_url.rstrip('/')}/archive/#week-{week}"


def project_site_url() -> str:
    try:
        config = load_yaml(ROOT / "mkdocs.yml")
    except FileNotFoundError:
        return ""
    if not isinstance(config, dict):
        return ""
    return str(config.get("site_url") or "").strip()


def mailing_record_path(week: str) -> Path:
    return MAILINGS_DIR / f"{week}.yml"


def load_mailing_record(week: str) -> dict[str, Any] | None:
    path = mailing_record_path(week)
    if not path.exists():
        return None
    data = load_yaml(path)
    if not isinstance(data, dict):
        raise ProjectError(f"{path}: mailing record must contain a mapping")
    return data


def assert_not_already_delivered(issue: NewsletterIssue, force: bool = False) -> None:
    record = load_mailing_record(issue.week)
    if not record:
        return

    status = str(record.get("status") or "")
    if status not in DELIVERED_STATUSES:
        return

    existing_hash = str(record.get("content_sha256") or "")
    if existing_hash == issue.content_sha256:
        if force:
            return
        raise ProjectError(f"{issue.week} was already delivered; use --force to send again.")

    if force:
        return
    raise ProjectError(
        f"{issue.week} was already delivered with different content; use --force only after confirming a re-send is intended."
    )


def write_mailing_record(issue: NewsletterIssue, provider: str, provider_message_id: str, status: str) -> None:
    now = project_now().isoformat(timespec="seconds")
    record = {
        "week": issue.week,
        "status": status,
        "paper_ids": issue.paper_ids,
        "content_sha256": issue.content_sha256,
        "sent_at": now if status in DELIVERED_STATUSES else "",
        "provider": provider,
        "provider_message_id": provider_message_id,
        "subject": issue.subject,
        "archive_url": issue.archive_url,
    }
    write_text(mailing_record_path(issue.week), yaml.safe_dump(record, sort_keys=False, allow_unicode=False))


def latest_delivered_week() -> str:
    delivered: list[tuple[str, str]] = []
    for path in sorted(MAILINGS_DIR.glob("*.yml")):
        data = load_yaml(path)
        if not isinstance(data, dict) or str(data.get("status") or "") not in DELIVERED_STATUSES:
            continue
        sent_at = str(data.get("sent_at") or "")
        delivered.append((sent_at, str(data.get("week") or path.stem)))
    if not delivered:
        return ""
    return sorted(delivered, reverse=True)[0][1]
