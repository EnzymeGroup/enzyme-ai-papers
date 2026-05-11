from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any

from newsletter import (
    NewsletterIssue,
    assert_not_already_delivered,
    build_newsletter_issue,
    previous_iso_week,
    write_mailing_record,
)
from paperlib import ProjectError, project_now


BUTTONDOWN_EMAILS_URL = "https://api.buttondown.com/v1/emails"


def main() -> int:
    parser = argparse.ArgumentParser(description="Send the weekly Enzyme AI Papers newsletter.")
    parser.add_argument("--week", help="ISO week to send, for example 2026-W18. Defaults to the previous ISO week.")
    parser.add_argument("--provider", default=os.environ.get("NEWSLETTER_PROVIDER", "buttondown"), choices=("buttondown",))
    parser.add_argument("--send", action="store_true", help="Create the provider email. Without this, only prints a dry run.")
    parser.add_argument("--draft", action="store_true", help="Create a provider draft instead of queueing it for delivery.")
    parser.add_argument("--test-recipient", help="Create a draft and send a preview copy to this email address only.")
    parser.add_argument("--force", action="store_true", help="Allow re-sending a week with an existing delivery record.")
    parser.add_argument("--print-body", action="store_true", help="Print the rendered email body during dry-run.")
    args = parser.parse_args()

    try:
        issue = build_newsletter_issue(args.week)
        if issue is None:
            week = args.week or previous_iso_week()
            print(f"No accepted papers for {week}; newsletter skipped.")
            return 0

        if args.test_recipient:
            provider_result = send_test_draft_with_buttondown(issue, args.test_recipient)
            print(f"Sent draft preview for {issue.week}: {issue.subject}")
            print(f"Recipient: {args.test_recipient}")
            print(f"Draft id: {provider_result.get('id') or '(not returned)'}")
            print(f"Content SHA-256: {issue.content_sha256}")
            return 0

        if not args.send:
            print_dry_run(issue, print_body=args.print_body)
            return 0

        assert_not_already_delivered(issue, force=args.force)
        provider_result = send_with_buttondown(issue, draft=args.draft)
        status = str(provider_result.get("status") or ("draft" if args.draft else "about_to_send"))
        provider_id = str(provider_result.get("id") or provider_result.get("slug") or "")
        write_mailing_record(issue, provider=args.provider, provider_message_id=provider_id, status=status)
        verb = "Created draft" if args.draft else "Queued delivery"
        print(f"{verb} for {issue.week}: {issue.subject}")
        print(f"Provider id: {provider_id or '(not returned)'}")
        print(f"Status: {status}")
        print(f"Content SHA-256: {issue.content_sha256}")
        return 0
    except ProjectError as error:
        print(str(error), file=sys.stderr)
        return 1


def print_dry_run(issue: NewsletterIssue, print_body: bool = False) -> None:
    print("Newsletter dry-run")
    print(f"Week: {issue.week}")
    print(f"Subject: {issue.subject}")
    print(f"Papers: {len(issue.paper_ids)}")
    print(f"Content SHA-256: {issue.content_sha256}")
    if issue.archive_url:
        print(f"Archive URL: {issue.archive_url}")
    if print_body:
        print()
        print(issue.body.rstrip())


def send_with_buttondown(issue: NewsletterIssue, draft: bool = False) -> dict[str, Any]:
    return create_buttondown_email(issue, draft=draft)


def send_test_draft_with_buttondown(issue: NewsletterIssue, recipient: str) -> dict[str, Any]:
    email = create_buttondown_email(issue, draft=True)
    email_id = str(email.get("id") or "")
    if not email_id:
        raise ProjectError("Buttondown did not return a draft email id.")

    payload = {"recipients": [recipient]}
    buttondown_request(f"{BUTTONDOWN_EMAILS_URL}/{email_id}/send-draft", payload)
    return email


def create_buttondown_email(issue: NewsletterIssue, draft: bool = False) -> dict[str, Any]:
    api_key = os.environ.get("BUTTONDOWN_API_KEY", "").strip()
    if not api_key:
        raise ProjectError("BUTTONDOWN_API_KEY is required for Buttondown delivery.")

    status = "draft" if draft else "about_to_send"
    slug = issue.slug if not draft else f"{issue.slug}-draft-{project_now().strftime('%Y%m%d%H%M%S')}"
    payload = {
        "subject": issue.subject,
        "body": issue.body,
        "status": status,
        "slug": slug,
        "email_type": "public",
        "metadata": {
            "project": "enzyme-ai-papers",
            "week": issue.week,
            "paper_ids": issue.paper_ids,
            "content_sha256": issue.content_sha256,
        },
    }
    if issue.archive_url:
        payload["canonical_url"] = issue.archive_url

    return buttondown_request(BUTTONDOWN_EMAILS_URL, payload, api_key=api_key, live_dangerously=not draft)


def buttondown_request(url: str, payload: dict[str, Any], api_key: str | None = None, live_dangerously: bool = False) -> dict[str, Any]:
    token = api_key or os.environ.get("BUTTONDOWN_API_KEY", "").strip()
    if not token:
        raise ProjectError("BUTTONDOWN_API_KEY is required for Buttondown API calls.")

    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json",
        "User-Agent": "enzyme-ai-papers/1.0",
    }
    if live_dangerously:
        headers["X-Buttondown-Live-Dangerously"] = "true"

    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            response_body = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise ProjectError(f"Buttondown API error {error.code}: {details}") from error
    except urllib.error.URLError as error:
        raise ProjectError(f"Buttondown API request failed: {error}") from error

    if not response_body.strip():
        return {}
    try:
        data = json.loads(response_body)
    except json.JSONDecodeError as error:
        raise ProjectError(f"Buttondown API returned invalid JSON: {response_body[:200]}") from error
    return data if isinstance(data, dict) else {"response": data}


if __name__ == "__main__":
    sys.exit(main())
