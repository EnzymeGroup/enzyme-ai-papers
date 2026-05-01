# Use Guideline

Short workflows for readers, submitters, and maintainers.

Authorized group maintainers can use GitHub Actions for direct publishing.
Public users should submit through the website or GitHub Issues.

## Read Papers

Purpose: find accepted enzyme AI papers quickly.

Flow:

1. Open the website or `README.md`.
2. Read the latest weekly issue first.
3. Use Archive to browse older papers.
4. Use search or tags to narrow by topic, method, evidence, or application.

## Subscribe to Weekly Email

Purpose: receive the weekly digest by email when a newsletter provider is
configured.

Flow:

1. Open the website Submit page.
2. Enter your email in the weekly email subscription form.
3. Confirm the subscription if the provider sends a confirmation email.
4. Use the provider unsubscribe link if you no longer want emails.

## Submit a Paper from the Website

Purpose: recommend a paper without editing the repository.

Flow:

1. Open the website Submit page.
2. Paste a public paper URL.
3. Optionally add a short note, tags, title, or code/project link.
4. Click `Open GitHub Submission`.
5. Submit the generated GitHub issue.
6. Wait for maintainer review.

## Submit a Paper from GitHub

Purpose: submit directly when you are already using the repository.

Flow:

1. Open GitHub Issues.
2. Choose the paper suggestion issue template.
3. Paste the paper URL.
4. Optionally add relevance notes, tags, or code links.
5. Submit the issue.

## Track a Submission

Purpose: know what happens after an issue is opened.

Flow:

1. Check the automatic metadata preview comment.
2. Reply if the preview misses important context.
3. Watch for a maintainer label: `accepted`, `needs-info`, or `rejected`.
4. If accepted, follow the linked curation pull request.

## Review a Paper as Maintainer

Purpose: decide whether a submitted paper should enter the digest.

Flow:

1. Open the paper suggestion issue.
2. Read the URL, submitter note, and metadata preview.
3. Check enzyme relevance, title, authors, DOI, links, and suggested tags.
4. Add `accepted` to generate a curation pull request.
5. Add `needs-info` if more context is needed.
6. Add `rejected` if the paper is out of scope.

## Merge an Accepted Paper

Purpose: publish a reviewed paper to the archive and website.

Flow:

1. Open the generated curation pull request.
2. Review the YAML record under `data/papers/YYYY/`.
3. Check the regenerated README and website pages.
4. Edit metadata if needed.
5. Wait for validation.
6. Merge the pull request.

## Submit Directly Through GitHub Actions

Purpose: let an authorized group maintainer publish a trusted paper URL without
opening a public suggestion issue.

Flow:

1. Make sure your GitHub username is listed in `ENZYME_PAPERS_DIRECT_PUBLISHERS`.
2. Open GitHub Actions.
3. Choose `Publish URL`.
4. Click `Run workflow`.
5. Paste the paper URL.
6. Optionally add title, note, tags, or code/project link.
7. Run the workflow.
8. Confirm the README and website update.

## Who Can Use Actions Directly

Purpose: keep direct publishing limited to trusted group maintainers.

Flow:

1. Ask a repository admin to add your GitHub username to `ENZYME_PAPERS_DIRECT_PUBLISHERS`.
2. Use a comma-separated value for multiple maintainers.
3. Example: `Jianxinnn,alice,bob`.
4. After that, you can run `Publish URL` and `Manage Paper`.
5. Being in the GitHub organization or group is not enough by itself.
6. If your username is not listed, the workflow will stop before publishing.

## Update a Published Paper Through GitHub Actions

Purpose: let an authorized group maintainer fix metadata without hand-editing
every generated file.

Flow:

1. Make sure your GitHub username is listed in `ENZYME_PAPERS_DIRECT_PUBLISHERS`.
2. Open GitHub Actions.
3. Choose `Manage Paper`.
4. Select `update`.
5. Enter the paper id, DOI, or URL.
6. Fill only the fields that should change.
7. Use `clear` for fields that should be emptied, such as `code,project,pdf`.
8. Run the workflow.
9. Confirm the README and website update.

## Delete a Published Paper Through GitHub Actions

Purpose: remove an incorrect or out-of-scope paper without hand-editing every
generated file.

Flow:

1. Make sure your GitHub username is listed in `ENZYME_PAPERS_DIRECT_PUBLISHERS`.
2. Open GitHub Actions.
3. Choose `Manage Paper`.
4. Select `delete`.
5. Enter the paper id, DOI, or URL in `selector`.
6. Leave the other fields empty.
7. Run the workflow.
8. Confirm the paper is gone from the README, website, and archive.

## Send or Preview the Weekly Newsletter

Purpose: let maintainers verify or send the weekly email without hand-writing
email content.

Flow:

1. Configure `BUTTONDOWN_API_KEY` as a GitHub Actions secret.
2. Optionally set `extra.newsletter.buttondown_username` in `mkdocs.yml` so the
   website shows a subscription form.
3. Set `extra.newsletter.subscribe_url` to the project website subscription
   page, not a Buttondown API or archive URL.
4. In Buttondown, set `subscription_redirect_url` and
   `subscription_confirmation_redirect_url` to the project website subscription
   page so successful subscription flows do not land on a Buttondown 404 while
   the account is under review.
5. Keep the Buttondown sender display name, `from_name`, set to `EnzymeGroup`.
6. Open GitHub Actions.
7. Choose `Weekly newsletter`.
8. Select `dry-run` to preview, `draft` to create a provider draft, or `send`
   to queue delivery.
9. Leave `week` blank to use the previous complete ISO week.
10. Run the workflow.
11. Check `data/mailings/YYYY-Www.yml` after a real send.

## Correct or Remove a Paper Manually

Purpose: use a pull request when GitHub Actions is not appropriate.

Flow:

1. Open an issue or pull request describing the change.
2. Edit or delete the paper record under `data/papers/YYYY/`.
3. Remove any related weekly override in `data/weekly/` if needed.
4. Run `python3 scripts/build_docs.py`.
5. Run `python3 scripts/validate_papers.py`.
6. Merge after validation passes.

## Important Rules

- Submit public `http` or `https` paper URLs only.
- Do not upload PDFs.
- Do not copy abstracts into curator notes.
- Do not accept broad protein papers unless enzyme relevance is clear.
- Do not edit generated README or docs without rebuilding from source data.
