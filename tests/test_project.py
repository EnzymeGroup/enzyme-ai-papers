from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class ProjectWorkflowTest(unittest.TestCase):
    def run_script(self, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        subprocess_env = os.environ.copy()
        if env:
            subprocess_env.update(env)
        return subprocess.run(
            [sys.executable, *args],
            cwd=ROOT,
            env=subprocess_env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_validate_script_passes(self) -> None:
        result = self.run_script("scripts/validate_papers.py")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Validation passed.", result.stdout)

    def test_build_docs_script_generates_expected_pages(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            shutil.copytree(ROOT / "data", project_root / "data")
            shutil.copytree(ROOT / "docs_src", project_root / "docs_src")
            shutil.copytree(ROOT / "schemas", project_root / "schemas")
            shutil.copy2(ROOT / "mkdocs.yml", project_root / "mkdocs.yml")

            result = self.run_script("scripts/build_docs.py", env={"ENZYME_PAPERS_ROOT": str(project_root)})
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            expected_paths = [
                project_root / "README.md",
                project_root / "docs" / "index.md",
                project_root / "docs" / "archive.md",
                project_root / "docs" / "subscribe.md",
                project_root / "docs" / "info.md",
                project_root / "docs" / "assets" / "title.svg",
                project_root / "docs" / "assets" / "site.css",
                project_root / "docs" / "assets" / "app.js",
            ]
            for path in expected_paths:
                self.assertTrue(path.exists(), f"Missing generated page: {path}")
                content = path.read_text(encoding="utf-8")
                self.assertTrue(content.strip(), f"Generated file is empty: {path}")

            index = (project_root / "docs" / "index.md").read_text(encoding="utf-8")
            archive = (project_root / "docs" / "archive.md").read_text(encoding="utf-8")
            subscribe = (project_root / "docs" / "subscribe.md").read_text(encoding="utf-8")
            info = (project_root / "docs" / "info.md").read_text(encoding="utf-8")
            readme = (project_root / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("Pick of the Week", index)
        self.assertNotIn("paper-toolbar", index)
        self.assertIn("weekly-paper-list", index)
        self.assertIn("brand-title", index)
        self.assertIn("paper-row", index)
        self.assertIn("paper-toolbar", archive)
        self.assertIn("Subscribe to Enzyme AI Papers", subscribe)
        self.assertIn("embed-subscribe/ecnu_enzyme", subscribe)
        self.assertIn("check your inbox and confirm the Buttondown email", subscribe)
        self.assertIn("paper-submit-form", info)
        self.assertIn("docs/assets/title.svg", readme)
        self.assertIn("Open GitHub Submission", info)
        self.assertIn("Enzyme AI Papers Weekly", readme)
        weekly_heading_pattern = (
            r"{label}: Enzyme AI Papers Weekly - \d{{4}}-W\d{{2}} "
            r"\(\d{{4}}\.\d{{1,2}}\.\d{{1,2}}-(?:\d{{4}}\.)?\d{{1,2}}\.\d{{1,2}}\)"
        )
        self.assertRegex(readme, weekly_heading_pattern.format(label="Latest Week"))
        self.assertRegex(readme, weekly_heading_pattern.format(label="Previous Week"))
        self.assertIn("2026-W17", archive)
        self.assertIn("2026.4.20-4.26", archive)
        self.assertNotIn("Pick of the Week", readme)
        self.assertNotIn("Directly published paper for enzyme AI curation", readme)
        self.assertNotIn("project owner URL workflow", index)
        self.assertIn("- Links: [Paper]", readme)
        self.assertIn("## Usage", readme)
        self.assertIn("USE_GUIDELINE.md", readme)
        self.assertIn("MORE_INFO.md", readme)
        self.assertNotIn("DEPLOYMENT.md", readme)
        self.assertNotIn("CURATION.md", readme)
        self.assertIn("Weekly email: [subscribe to the digest](https://enzymegroup.github.io/enzyme-ai-papers/subscribe/).", readme)

    def test_schema_contract_matches_validator(self) -> None:
        sys.path.insert(0, str(ROOT / "scripts"))
        from paperlib import validate_schema_contract

        self.assertEqual(validate_schema_contract(), [])

    def test_fetch_candidates_is_safe_placeholder(self) -> None:
        result = self.run_script("scripts/fetch_candidates.py")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("disabled", result.stdout)

    def test_accepted_datetimes_use_project_timezone(self) -> None:
        sys.path.insert(0, str(ROOT / "scripts"))
        from paperlib import iso_week, parse_record_date

        accepted_at = "2026-04-26T17:38:37+00:00"
        self.assertEqual(parse_record_date(accepted_at).isoformat(), "2026-04-27")
        self.assertEqual(iso_week(accepted_at), "2026-W18")

    def test_sorted_papers_puts_newest_acceptance_first(self) -> None:
        sys.path.insert(0, str(ROOT / "scripts"))
        from paperlib import PaperRecord, sorted_papers

        older = PaperRecord(
            Path("older.yml"),
            {
                "id": "older",
                "title": "Older accepted paper",
                "year": 2026,
                "date": "2026-04-27",
                "accepted_at": "2026-04-27T01:00:00+08:00",
            },
        )
        newer = PaperRecord(
            Path("newer.yml"),
            {
                "id": "newer",
                "title": "Newer accepted paper",
                "year": 2026,
                "date": "2026-04-27",
                "accepted_at": "2026-04-27T02:00:00+08:00",
            },
        )

        self.assertEqual([record.paper_id for record in sorted_papers([older, newer])], ["newer", "older"])

    def test_newsletter_renders_previous_week_digest(self) -> None:
        sys.path.insert(0, str(ROOT / "scripts"))
        from datetime import date

        from newsletter import build_newsletter_issue, previous_iso_week

        self.assertEqual(previous_iso_week(date(2026, 5, 4)), "2026-W18")
        issue = build_newsletter_issue("2026-W18")

        self.assertIsNotNone(issue)
        assert issue is not None
        self.assertEqual(issue.week, "2026-W18")
        self.assertEqual(len(issue.paper_ids), 5)
        self.assertIn("Enzyme AI Papers Weekly - 2026-W18", issue.subject)
        self.assertIn("## Papers", issue.body)
        self.assertIn("https://enzymegroup.github.io/enzyme-ai-papers/archive/#week-2026-W18", issue.body)
        self.assertRegex(issue.content_sha256, r"^[0-9a-f]{64}$")

    def test_send_weekly_email_dry_run_does_not_need_provider_secret(self) -> None:
        result = self.run_script("scripts/send_weekly_email.py", "--week", "2026-W18")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Newsletter dry-run", result.stdout)
        self.assertIn("Week: 2026-W18", result.stdout)
        self.assertIn("Papers: 5", result.stdout)
        self.assertIn("Content SHA-256:", result.stdout)

    def test_send_weekly_email_send_requires_provider_secret(self) -> None:
        result = self.run_script("scripts/send_weekly_email.py", "--week", "2026-W18", "--send", env={"BUTTONDOWN_API_KEY": ""})

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("BUTTONDOWN_API_KEY is required", result.stderr)

    def test_newsletter_workflow_does_not_hide_delivery_errors(self) -> None:
        import yaml

        workflow = yaml.safe_load((ROOT / ".github" / "workflows" / "newsletter.yml").read_text(encoding="utf-8"))
        send_step = next(step for step in workflow["jobs"]["newsletter"]["steps"] if step.get("name") == "Send weekly newsletter")

        self.assertIn("set -o pipefail", send_step["run"])
        self.assertNotIn("newsletter skipped", send_step["run"])

    def test_buttondown_send_includes_live_confirmation_header(self) -> None:
        sys.path.insert(0, str(ROOT / "scripts"))
        from newsletter import NewsletterIssue
        from send_weekly_email import create_buttondown_email

        captured_headers = {}

        class FakeResponse:
            def __enter__(self) -> "FakeResponse":
                return self

            def __exit__(self, *args: object) -> None:
                return None

            def read(self) -> bytes:
                return b'{"id":"email_123","status":"about_to_send"}'

        def fake_urlopen(request: object, timeout: int) -> FakeResponse:
            captured_headers.update(dict(request.header_items()))
            self.assertEqual(timeout, 30)
            return FakeResponse()

        issue = NewsletterIssue(
            week="2026-W19",
            title="Enzyme AI Papers Weekly - 2026-W19",
            date_range="2026.5.4-5.10",
            summary="Summary",
            subject="Enzyme AI Papers Weekly - 2026-W19",
            body="Body",
            paper_ids=["paper-1"],
            content_sha256="abc123",
            archive_url="https://example.org/archive/#week-2026-W19",
        )
        with patch.dict(os.environ, {"BUTTONDOWN_API_KEY": "test-key"}), patch("urllib.request.urlopen", fake_urlopen):
            result = create_buttondown_email(issue)

        self.assertEqual(result["status"], "about_to_send")
        self.assertEqual(captured_headers["X-buttondown-live-dangerously"], "true")

    def test_metadata_helpers_clean_common_publisher_values(self) -> None:
        sys.path.insert(0, str(ROOT / "scripts"))
        from issue_tools import (
            clean_metadata_text,
            extract_sciencedirect_pii,
            fetch_biorxiv_metadata,
            infer_url_metadata,
            metadata_from_crossref_message,
            normalize_preprint_doi,
            parse_metadata_date,
            unique_values,
        )

        self.assertEqual(clean_metadata_text("The <i>LDLR</i> landscape"), "The LDLR landscape")
        self.assertEqual(unique_values(["Zhu, Xin-Xin", " Zhu, Xin-Xin ", "Kong, Xu-Dong"]), ["Zhu, Xin-Xin", "Kong, Xu-Dong"])
        self.assertEqual(parse_metadata_date("28 November 2024"), "2024-11-28")
        self.assertEqual(extract_sciencedirect_pii("https://www.sciencedirect.com/science/article/pii/S2211383526000778"), "S2211383526000778")
        self.assertEqual(normalize_preprint_doi("10.64898/2026.05.01.722313v2.abstract"), "10.64898/2026.05.01.722313")
        self.assertEqual(normalize_preprint_doi("10.64898/2026.05.01.722313v2.full.pdf"), "10.64898/2026.05.01.722313")

        preprint_metadata = infer_url_metadata("https://www.biorxiv.org/content/10.64898/2026.05.01.722313v2.abstract")
        self.assertEqual(preprint_metadata["doi"], "10.64898/2026.05.01.722313")
        self.assertEqual(preprint_metadata["identifier"], "doi-10-64898-2026-05-01-722313")
        with patch(
            "issue_tools.fetch_json",
            return_value={
                "collection": [
                    {
                        "title": "Simple baselines rival protein language models",
                        "authors": "Talpir, I.; Fleishman, S. J.",
                        "date": "2026-05-08",
                        "version": "2",
                    }
                ]
            },
        ):
            fetched_preprint = fetch_biorxiv_metadata("10.64898/2026.05.01.722313v2.abstract", "biorxiv")
        self.assertEqual(fetched_preprint["url"], "https://www.biorxiv.org/content/10.64898/2026.05.01.722313v2")
        self.assertEqual(fetched_preprint["pdf"], "https://www.biorxiv.org/content/10.64898/2026.05.01.722313v2.full.pdf")

        metadata = metadata_from_crossref_message(
            {
                "DOI": "10.1126/science.ady7186",
                "title": ["The functional landscape of <i>LDLR</i>"],
                "container-title": ["Science"],
                "published-online": {"date-parts": [[2026, 2, 19]]},
                "author": [
                    {"given": "Daniel R.", "family": "Tabet"},
                    {"given": "Daniel R.", "family": "Tabet"},
                ],
                "URL": "https://doi.org/10.1126/science.ady7186",
            }
        )

        self.assertEqual(metadata["title"], "The functional landscape of LDLR")
        self.assertEqual(metadata["authors"], ["Daniel R. Tabet"])
        self.assertEqual(metadata["date"], "2026-02-19")
        self.assertEqual(metadata["identifier"], "doi-10-1126-science-ady7186")

    def test_preview_issue_accepts_url_only_submission(self) -> None:
        event = {
            "issue": {
                "number": 42,
                "title": "[Paper]: Example enzyme paper",
                "body": "### Paper URL\n\nhttps://doi.org/10.1234/example.paper\n\n### Why this paper matters\n\n_No response_",
                "labels": [{"name": "needs-review"}],
                "user": {"login": "submitter"},
            },
            "sender": {"login": "maintainer"},
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            event_path = Path(tmpdir) / "event.json"
            event_path.write_text(json.dumps(event), encoding="utf-8")
            result = self.run_script("scripts/preview_issue.py", "--event", str(event_path))

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Paper suggestion preview", result.stdout)
        self.assertIn("https://doi.org/10.1234/example.paper", result.stdout)
        self.assertIn("`accepted`", result.stdout)

    def test_accept_issue_ignores_unaccepted_issue(self) -> None:
        event = {
            "issue": {
                "number": 43,
                "title": "[Paper]: Example enzyme paper",
                "body": "### Paper URL\n\nhttps://example.org/paper",
                "labels": [{"name": "needs-review"}],
                "user": {"login": "submitter"},
            },
            "sender": {"login": "maintainer"},
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            event_path = Path(tmpdir) / "event.json"
            event_path.write_text(json.dumps(event), encoding="utf-8")
            result = self.run_script("scripts/accept_issue.py", "--event", str(event_path))

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("not labeled accepted", result.stdout)

    def test_preview_issue_rejects_local_urls(self) -> None:
        event = {
            "issue": {
                "number": 44,
                "title": "[Paper]: Local URL",
                "body": "### Paper URL\n\nhttp://127.0.0.1:8000/paper",
                "labels": [{"name": "needs-review"}],
                "user": {"login": "submitter"},
            },
            "sender": {"login": "maintainer"},
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            event_path = Path(tmpdir) / "event.json"
            event_path.write_text(json.dumps(event), encoding="utf-8")
            result = self.run_script("scripts/preview_issue.py", "--event", str(event_path))

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("not a public web URL", result.stdout)

    def test_accept_issue_rejects_local_urls(self) -> None:
        event = {
            "issue": {
                "number": 45,
                "title": "[Paper]: Local URL",
                "body": "### Paper URL\n\nhttp://localhost/paper",
                "labels": [{"name": "accepted"}],
                "user": {"login": "submitter"},
            },
            "sender": {"login": "maintainer"},
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            event_path = Path(tmpdir) / "event.json"
            event_path.write_text(json.dumps(event), encoding="utf-8")
            result = self.run_script("scripts/accept_issue.py", "--event", str(event_path))

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("public paper URL", result.stderr)

    def test_publish_url_dry_run_generates_paper_yaml(self) -> None:
        result = self.run_script(
            "scripts/publish_url.py",
            "--url",
            "https://doi.org/10.1234/direct.publish.example",
            "--title",
            "Direct Publish Example Paper",
            "--note",
            "Demonstrates owner-only direct URL publishing.",
            "--tags",
            "enzyme design, benchmark",
            "--reviewer",
            "maintainer",
            "--accepted-at",
            "2026-04-26T00:00:00+00:00",
            "--dry-run",
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("id: doi-10-1234-direct-publish-example", result.stdout)
        self.assertIn("title: Direct Publish Example Paper", result.stdout)
        self.assertIn("curator: maintainer", result.stdout)
        self.assertIn("featured: false", result.stdout)
        self.assertIn("https://doi.org/10.1234/direct.publish.example", result.stdout)

    def test_manage_paper_dry_run_updates_existing_metadata(self) -> None:
        result = self.run_script(
            "scripts/manage_paper.py",
            "--selector",
            "doi-10-64898-2026-04-23-719915",
            "--one-liner",
            "Updated direct management summary.",
            "--featured",
            "false",
            "--reviewer",
            "maintainer",
            "--dry-run",
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("id: doi-10-64898-2026-04-23-719915", result.stdout)
        self.assertIn("one_liner: Updated direct management summary.", result.stdout)
        self.assertIn("featured: false", result.stdout)

    def test_manage_paper_dry_run_can_select_by_url_for_delete(self) -> None:
        result = self.run_script(
            "scripts/manage_paper.py",
            "--selector",
            "https://www.biorxiv.org/content/10.64898/2026.04.23.719915v1",
            "--delete",
            "--dry-run",
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Would delete paper: doi-10-64898-2026-04-23-719915", result.stdout)


if __name__ == "__main__":
    unittest.main()
