from __future__ import annotations

import html
from collections import defaultdict
from typing import Any

from docs_config import PAGE_PREFIX
from docs_weeklies import readme_week_label
from paperlib import (
    DOCS_DIR,
    ROOT,
    TAG_GROUPS,
    display_note,
    display_summary,
    load_yaml,
    write_text,
)


def build_home_page(latest: dict[str, Any] | None, paper_index: dict[str, Any]) -> None:
    if latest is None:
        issue = None
        main_content = """
<section class="empty-state">
  <h2>No weekly issue yet</h2>
  <p>Accept a paper suggestion issue to publish the first automatically generated weekly digest.</p>
</section>
"""
    else:
        issue = latest
        main_content = render_weekly(latest, paper_index)

    content = f"""{PAGE_PREFIX}{render_page_shell("weekly", issue)}

{main_content}
"""
    write_text(DOCS_DIR / "index.md", content.rstrip() + "\n")


def build_archive_page(
    papers: list[Any],
    paper_index: dict[str, Any],
    weeklies: list[dict[str, Any]],
    latest: dict[str, Any] | None,
) -> None:
    by_year: dict[int, list[Any]] = defaultdict(list)
    for paper in papers:
        by_year[paper.year].append(paper)

    groups: list[str] = []
    for year in sorted(by_year.keys(), reverse=True):
        cards = "\n".join(render_paper_card(record) for record in by_year[year])
        groups.append(
            f"""
<section class="paper-group">
  <div class="section-label">{year}</div>
  <div class="paper-grid">
    {cards}
  </div>
</section>
"""
        )

    content = f"""{PAGE_PREFIX}{render_page_shell("archive", latest)}

{render_toolbar(papers)}

{render_weekly_history(weeklies)}

{render_weekly_archive(weeklies, paper_index)}

{''.join(groups) if groups else '<section class="empty-state"><h2>No papers yet</h2></section>'}
"""
    write_text(DOCS_DIR / "archive.md", content.rstrip() + "\n")


def build_info_page(issue: dict[str, Any] | None) -> None:
    issue_url = issue_submission_url()
    content = f"""{PAGE_PREFIX}{render_page_shell("submit", issue)}

{render_submit_form(issue_url)}

<section class="info-grid">
  <article class="info-block">
    <h2>Readers</h2>
    <p>Start with the latest weekly issue. Use the archive when you want to browse by tag or keyword.</p>
  </article>
  <article class="info-block">
    <h2>Submitters</h2>
    <p>Open a GitHub issue with a paper URL. Notes, tags, title, code, and project links are optional.</p>
  </article>
  <article class="info-block">
    <h2>Maintainers</h2>
    <p>Review the issue preview, add <code>accepted</code> to include it, and adjust generated metadata before merging.</p>
  </article>
</section>

<section class="command-block">
  <h2>Automation</h2>
  <pre><code>Issue opened -> metadata preview
Label accepted -> paper YAML draft + generated weekly digest
Pull request -> validation + MkDocs build</code></pre>
</section>
"""
    write_text(DOCS_DIR / "info.md", content.rstrip() + "\n")


def build_subscribe_page(issue: dict[str, Any] | None) -> None:
    content = f"""{PAGE_PREFIX}{render_page_shell("subscribe", issue)}

{render_newsletter_signup()}

<section class="info-grid">
  <article class="info-block">
    <h2>Weekly digest</h2>
    <p>New accepted enzyme AI and computational enzyme papers are sent when a weekly issue is available.</p>
  </article>
  <article class="info-block">
    <h2>Privacy boundary</h2>
    <p>Subscriber addresses, confirmations, and unsubscribes are handled by Buttondown, not this repository.</p>
  </article>
</section>
"""
    write_text(DOCS_DIR / "subscribe.md", content.rstrip() + "\n")


def render_newsletter_signup() -> str:
    config = newsletter_config()
    username = str(config.get("buttondown_username") or "").strip()
    subscribe_url = str(config.get("subscribe_url") or "").strip()
    if username:
        action = f"https://buttondown.com/api/emails/embed-subscribe/{escape(username)}"
        return f"""
<section class="newsletter-panel">
  <form class="newsletter-form embeddable-buttondown-form" action="{escape(action)}" method="post">
    <div>
      <div class="section-label">Weekly email</div>
      <h2>Subscribe to Enzyme AI Papers</h2>
      <p>Get the weekly digest when new accepted papers are available.</p>
    </div>
    <label for="newsletter-email">Email</label>
    <div class="newsletter-controls">
      <input id="newsletter-email" type="email" name="email" required placeholder="you@example.com">
      <input type="hidden" value="1" name="embed">
      <button type="submit">Subscribe</button>
    </div>
    <p class="newsletter-note">Subscriptions, confirmations, and unsubscribes are handled by Buttondown. After subscribing, check your inbox and confirm the Buttondown email.</p>
  </form>
</section>
"""
    if subscribe_url:
        return f"""
<section class="newsletter-panel">
  <div class="newsletter-form">
    <div>
      <div class="section-label">Weekly email</div>
      <h2>Subscribe to Enzyme AI Papers</h2>
      <p>Get the weekly digest when new accepted papers are available.</p>
    </div>
    <a class="newsletter-button" href="{escape(subscribe_url)}">Subscribe</a>
    <p class="newsletter-note">After subscribing, check your inbox and confirm the Buttondown email.</p>
  </div>
</section>
"""
    return ""


def newsletter_config() -> dict[str, Any]:
    config = load_yaml(ROOT / "mkdocs.yml")
    if not isinstance(config, dict):
        return {}
    extra = config.get("extra")
    if not isinstance(extra, dict):
        return {}
    newsletter = extra.get("newsletter")
    return newsletter if isinstance(newsletter, dict) else {}


def render_weekly(weekly: dict[str, Any], paper_index: dict[str, Any]) -> str:
    commentary = weekly.get("commentary", {})
    rows = "\n".join(render_weekly_paper_row(paper_index[paper_id], commentary.get(paper_id)) for paper_id in weekly["paper_ids"])
    return f"""
<section class="weekly-overview">
  <div class="section-label">{escape(readme_week_label(weekly, 0))}</div>
  <h2>{escape(weekly['title'])}</h2>
  <p class="weekly-range">{escape(weekly['week'])}: {escape(weekly['date_range'])}</p>
  <p class="weekly-summary">{escape(weekly['summary'])}</p>
</section>

<section class="weekly-paper-section" id="weekly-papers">
  <div class="section-label">Papers</div>
  <div class="weekly-paper-list">
{rows}
  </div>
</section>
"""


def render_submit_form(issue_url: str) -> str:
    return f"""
<section class="submit-panel">
  <form id="paper-submit-form" class="submit-form" data-issue-url="{escape(issue_url)}">
    <div>
      <div class="section-label">Submit paper</div>
      <h2>Share a paper URL</h2>
    </div>
    <label for="submit-paper-url">Paper URL</label>
    <input id="submit-paper-url" name="url" type="url" required placeholder="https://doi.org/...">
    <label for="submit-paper-title">Title</label>
    <input id="submit-paper-title" name="title" type="text" placeholder="Optional">
    <label for="submit-paper-note">Why this paper matters</label>
    <textarea id="submit-paper-note" name="note" rows="4" placeholder="Optional"></textarea>
    <label for="submit-paper-tags">Tags</label>
    <input id="submit-paper-tags" name="tags" type="text" placeholder="enzyme design, PLM, wet lab validation">
    <label for="submit-paper-code">Code or project link</label>
    <input id="submit-paper-code" name="code" type="url" placeholder="https://github.com/...">
    <div class="submit-actions">
      <button type="submit">Open GitHub Submission</button>
      <a href="{escape(issue_url)}">Open blank issue</a>
    </div>
    <p id="submit-form-status" class="form-status" aria-live="polite"></p>
  </form>
  <aside class="review-boundary">
    <div class="section-label">Review boundary</div>
    <ul>
      <li>Submissions open as GitHub issues under the submitter account.</li>
      <li>The website does not store a GitHub token or write repository data.</li>
      <li>Only maintainers can apply curation labels such as <code>accepted</code>.</li>
      <li>Accepted papers are generated through a pull request and validation checks.</li>
    </ul>
  </aside>
</section>
"""


def issue_submission_url() -> str:
    config = load_yaml(ROOT / "mkdocs.yml")
    repo_url = ""
    if isinstance(config, dict):
        repo_url = str(config.get("repo_url") or "").rstrip("/")
    if not repo_url:
        repo_url = "https://github.com/your-org/enzyme-ai-papers"
    return f"{repo_url}/issues/new"


def render_weekly_history(weeklies: list[dict[str, Any]]) -> str:
    if not weeklies:
        return ""
    links = "\n".join(
        f'<a class="weekly-link" href="#week-{escape(weekly["week"])}"><strong>{escape(weekly["week"])}</strong><span>{escape(str(weekly["date_range"]))}</span></a>'
        for weekly in weeklies
    )
    return f"""
<section class="weekly-history">
  <div class="section-label">Weekly issues</div>
  <div class="weekly-links">
    {links}
  </div>
</section>
"""


def render_weekly_archive(weeklies: list[dict[str, Any]], paper_index: dict[str, Any]) -> str:
    if not weeklies:
        return ""
    chunks = ['<section class="paper-sections weekly-archive">']
    for weekly in weeklies:
        commentary = weekly.get("commentary", {})
        cards = "\n".join(render_paper_card(paper_index[paper_id], commentary.get(paper_id)) for paper_id in weekly["paper_ids"])
        chunks.append(
            f"""
  <section class="paper-group" id="week-{escape(weekly['week'])}">
    <div class="section-label">{escape(weekly['week'])}: {escape(weekly['date_range'])}</div>
    <h2>{escape(weekly['title'])}</h2>
    <p class="weekly-summary">{escape(weekly['summary'])}</p>
    <div class="paper-grid">{cards}</div>
  </section>
"""
        )
    chunks.append("</section>")
    return "\n".join(chunks)


def render_toolbar(papers: list[Any]) -> str:
    return f"""
<section class="paper-toolbar" aria-label="Paper filters">
  <label class="search-label" for="paper-search">Search</label>
  <input id="paper-search" type="search" placeholder="Search title, tag, note, author">
  <button class="filter-chip is-active" data-filter="all" type="button">All</button>
  {render_filter_buttons(papers)}
</section>
"""


def render_page_shell(active: str, issue: dict[str, Any] | None) -> str:
    if active == "weekly":
        links = {"weekly": "./", "archive": "archive/", "subscribe": "subscribe/", "submit": "info/"}
        logo_src = "assets/title.svg"
    elif active == "archive":
        links = {"weekly": "../", "archive": "./", "subscribe": "../subscribe/", "submit": "../info/"}
        logo_src = "../assets/title.svg"
    elif active == "subscribe":
        links = {"weekly": "../", "archive": "../archive/", "subscribe": "./", "submit": "../info/"}
        logo_src = "../assets/title.svg"
    else:
        links = {"weekly": "../", "archive": "../archive/", "subscribe": "../subscribe/", "submit": "./"}
        logo_src = "../assets/title.svg"

    return f"""
<section class="brand-title" aria-label="Enzyme AI Papers">
  <img src="{logo_src}" alt="Enzyme AI Papers" loading="eager">
</section>

<section class="paper-start">
  <nav class="paper-switcher" aria-label="Section navigation">
    {render_switch_item("weekly", "Weekly", links["weekly"], active)}
    {render_switch_item("archive", "Archive", links["archive"], active)}
    {render_switch_item("subscribe", "Subscribe", links["subscribe"], active)}
    {render_switch_item("submit", "Submit", links["submit"], active)}
  </nav>
  {render_issue_card(issue)}
</section>
"""


def render_switch_item(key: str, label: str, href: str, active: str) -> str:
    classes = "switch-item is-active" if key == active else "switch-item"
    return f"""
<a class="{classes}" href="{href}">
  <span class="switch-icon">{nav_icon(key)}</span>
  <strong>{escape(label)}</strong>
</a>
"""


def render_issue_card(issue: dict[str, Any] | None) -> str:
    if issue is None:
        return """
<aside class="issue-card">
  <span class="issue-kicker">Latest issue</span>
  <strong>No issue yet</strong>
  <p>Accept a paper suggestion to publish the first issue.</p>
</aside>
"""

    return f"""
<aside class="issue-card">
  <span class="issue-kicker">Latest issue</span>
  <strong>{escape(issue['week'])}</strong>
  <span class="issue-range">{escape(issue['date_range'])}</span>
</aside>
"""


def render_filter_buttons(papers: list[Any]) -> str:
    seen: list[str] = []
    for paper in papers:
        for group in TAG_GROUPS:
            for tag in paper.data.get(group, []):
                if tag not in seen:
                    seen.append(tag)
    return "\n  ".join(
        f'<button class="filter-chip" data-filter="{escape(tag)}" type="button">{escape(tag)}</button>'
        for tag in seen[:12]
    )


def render_weekly_paper_row(record: Any, commentary: str | None = None) -> str:
    paper = record.data
    tags: list[str] = []
    for group in TAG_GROUPS:
        tags.extend(str(tag) for tag in paper.get(group, []))

    authors = ", ".join(paper.get("authors", []))
    summary = display_summary(paper)
    note = display_note(paper, commentary)
    tag_html = "".join(f"<span>{escape(tag)}</span>" for tag in tags)
    link_html = html_links(paper)
    summary_html = f'    <p class="summary">{escape(summary)}</p>\n' if summary else ""
    note_html = f'    <p class="why">{escape(note)}</p>\n' if note else ""
    links_html = f'  <div class="paper-links">{link_html}</div>\n' if link_html else ""

    return f"""
<article class="paper-row">
  <div class="paper-row-main">
    <div class="paper-meta">
      <span>{escape(paper['source'])}</span>
      <span>{escape(str(paper['year']))}</span>
    </div>
    <h3>{escape(paper['title'])}</h3>
    <p class="authors">{escape(authors)}</p>
{summary_html}{note_html}    <div class="tags">{tag_html}</div>
  </div>
{links_html}</article>
"""


def render_paper_card(record: Any, commentary: str | None = None) -> str:
    paper = record.data
    tags: list[str] = []
    for group in TAG_GROUPS:
        tags.extend(str(tag) for tag in paper.get(group, []))

    authors = ", ".join(paper.get("authors", []))
    summary = display_summary(paper)
    note = display_note(paper, commentary)
    tag_html = "".join(f"<span>{escape(tag)}</span>" for tag in tags)
    link_html = html_links(paper)
    summary_html = f'  <p class="summary">{escape(summary)}</p>\n' if summary else ""
    note_html = f'  <p class="why">{escape(note)}</p>\n' if note else ""
    links_html = f'  <div class="paper-links">{link_html}</div>\n' if link_html else ""
    searchable = " ".join(part for part in [paper["title"], authors, summary, note, " ".join(tags)] if part)

    return f"""
<article class="paper-card" data-tags="{escape(' '.join(tags))}" data-search="{escape(searchable.lower())}">
  <div class="paper-meta">
    <span>{escape(paper['source'])}</span>
    <span>{escape(str(paper['year']))}</span>
  </div>
  <h3>{escape(paper['title'])}</h3>
  <p class="authors">{escape(authors)}</p>
{summary_html}{note_html}  <div class="tags">{tag_html}</div>
{links_html}</article>
"""


def html_links(paper: dict[str, Any]) -> str:
    items = []
    for field, label in (
        ("url", "Paper"),
        ("pdf", "PDF"),
        ("code", "Code"),
        ("project", "Project"),
    ):
        value = paper.get(field)
        if value:
            items.append(f'<a href="{escape(value)}">{link_icon(field)}<span>{label}</span></a>')
    return "".join(items)


def link_icon(field: str) -> str:
    icons = {
        "url": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h8l4 4v14H6z"/><path d="M14 3v5h5"/><path d="M9 13h6M9 17h6"/></svg>',
        "pdf": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h8l4 4v14H6z"/><path d="M14 3v5h5"/><path d="M8.5 16h7"/></svg>',
        "code": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2a10 10 0 0 0-3.2 19.5c.5.1.7-.2.7-.5v-1.8c-2.8.6-3.4-1.2-3.4-1.2-.5-1.1-1.1-1.4-1.1-1.4-.9-.6.1-.6.1-.6 1 .1 1.6 1.1 1.6 1.1.9 1.5 2.4 1.1 2.9.8.1-.7.4-1.1.7-1.4-2.2-.3-4.6-1.1-4.6-4.9 0-1.1.4-2 1.1-2.7-.1-.3-.5-1.3.1-2.7 0 0 .9-.3 2.8 1a9.6 9.6 0 0 1 5.1 0c1.9-1.3 2.8-1 2.8-1 .6 1.4.2 2.4.1 2.7.7.7 1.1 1.6 1.1 2.7 0 3.8-2.3 4.6-4.6 4.9.4.3.8 1 .8 2v2.5c0 .3.2.6.8.5A10 10 0 0 0 12 2z"/></svg>',
        "project": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5h16v14H4z"/><path d="M4 9h16"/><path d="M8 13h3M8 16h7"/></svg>',
    }
    return icons.get(field, icons["url"])


def nav_icon(key: str) -> str:
    icons = {
        "weekly": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h12v18l-6-3-6 3z"/><path d="M9 8h6M9 11h6"/></svg>',
        "archive": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5h16v4H4z"/><path d="M6 9h12v10H6z"/><path d="M10 13h4"/></svg>',
        "subscribe": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16v12H4z"/><path d="m4 7 8 6 8-6"/><path d="M7 16h10"/></svg>',
        "submit": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4v12"/><path d="M7 9l5-5 5 5"/><path d="M5 20h14"/></svg>',
    }
    return icons[key]


def escape(value: Any) -> str:
    return html.escape(str(value), quote=True)
