from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Any

from paperlib import load_weeklies, parse_record_date, sorted_papers


def derive_weeklies(papers: list[Any]) -> list[dict[str, Any]]:
    overrides = {record.week: record.data for record in load_weeklies()}
    by_week: dict[str, list[Any]] = defaultdict(list)
    for paper in papers:
        by_week[paper.week].append(paper)

    weeklies: list[dict[str, Any]] = []
    for week, records in by_week.items():
        sorted_records = sorted_papers(records)
        override = overrides.get(week, {})
        commentary = override.get("commentary", {}) if isinstance(override, dict) else {}
        latest_date = max(parse_record_date(record.accepted_at) for record in sorted_records).isoformat()
        week_start, week_end = iso_week_bounds(week)
        weeklies.append(
            {
                "week": week,
                "title": override.get("title", f"Enzyme AI Papers Weekly - {week}")
                if isinstance(override, dict)
                else f"Enzyme AI Papers Weekly - {week}",
                "date": override.get("date", latest_date) if isinstance(override, dict) else latest_date,
                "start_date": week_start.isoformat(),
                "end_date": week_end.isoformat(),
                "date_range": format_week_range(week),
                "summary": override.get("summary", auto_summary(week, sorted_records))
                if isinstance(override, dict)
                else auto_summary(week, sorted_records),
                "paper_ids": [record.paper_id for record in sorted_records],
                "commentary": commentary if isinstance(commentary, dict) else {},
            }
        )

    return sorted(weeklies, key=lambda record: record["week"], reverse=True)


def auto_summary(week: str, records: list[Any]) -> str:
    count = len(records)
    noun = "paper" if count == 1 else "papers"
    return f"{count} accepted enzyme AI or computational enzyme {noun} collected for {week}."


def iso_week_bounds(week: str) -> tuple[date, date]:
    match = week.split("-W", 1)
    if len(match) != 2:
        raise ValueError(f"invalid ISO week: {week}")
    start = date.fromisocalendar(int(match[0]), int(match[1]), 1)
    return start, start + timedelta(days=6)


def format_week_range(week: str) -> str:
    start, end = iso_week_bounds(week)
    if start.year == end.year:
        return f"{format_dot_date(start)}-{end.month}.{end.day}"
    return f"{format_dot_date(start)}-{format_dot_date(end)}"


def format_dot_date(value: date) -> str:
    return f"{value.year}.{value.month}.{value.day}"


def readme_week_label(weekly: dict[str, Any], index: int) -> str:
    return "Latest Week" if index == 0 else "Previous Week"
