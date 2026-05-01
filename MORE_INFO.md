# Usage Guide

Enzyme AI Papers is a curated weekly digest for enzyme AI and computational
enzyme research. The normal workflow is:

```text
Paper URL -> GitHub issue preview -> maintainer review -> generated pull request -> weekly digest
```

## Read Papers

- Start with the latest weekly issue on the website or in `README.md`.
- Use the archive page to browse older papers and weekly history.
- Use search and tags to narrow papers by task, method, evidence, or
  application.
- Subscribe to the weekly email if a maintainer has configured the newsletter
  provider.

## Submit a Paper

Use the website Submit page or open a GitHub paper suggestion issue with a
paper URL.

Required:

- Paper URL.

Optional:

- A short note explaining why the paper matters.
- Suggested free-text tags.
- Code, project, dataset, or benchmark link.
- A title if the source metadata may be hard to parse.

The website form only opens a prefilled GitHub issue. It does not store
credentials, call the GitHub API, or write accepted paper data.

## Maintainer Review

Maintainers review the automatic issue preview and use labels as the curation
interface:

- `accepted`: include the paper in the archive.
- `needs-info`: ask the submitter for more context.
- `rejected`: decline the suggestion.

When `accepted` is applied, automation creates a curation pull request with the
paper record and regenerated website pages. Before merging, check the title,
authors, DOI, source, links, tags, one-line summary, and curator note.

Accepted papers live under `data/papers/YYYY/`. Weekly issues are generated
from accepted paper records using `accepted_at`; `data/weekly/` is only for
optional curator overrides such as custom commentary.

## Weekly Email

The email newsletter is another publishing surface for the same derived weekly
digest. It does not store subscriber addresses in the repository. Subscription,
unsubscribe, and delivery preferences are handled by the configured newsletter
provider.

Maintainers can preview or send a week through the `Weekly newsletter` GitHub
Actions workflow. The workflow defaults to the previous complete ISO week,
skips weeks with no accepted papers, and records real deliveries under
`data/mailings/`.

## Curation Scope

Accept papers with a clear connection to enzyme AI or computational enzyme
research, including:

- Enzyme design or redesign.
- Enzyme function prediction.
- Substrate specificity.
- Catalytic site discovery or engineering.
- Enzyme stability, expression, or activity optimization.
- Directed evolution with computational or AI support.
- Computational biocatalysis.
- Enzyme datasets, benchmarks, or reusable tools.
- Important reviews or perspectives for enzyme AI.

Do not accept papers that are only weakly related, such as:

- General protein design papers with no enzyme-specific relevance.
- Generic docking or molecular modeling papers without an enzyme application.
- News, blog posts, or press releases without a primary paper.
- Papers where enzyme relevance is only a minor keyword.
- Duplicates of an existing preprint or published record.

Curator notes should be short and original. Explain what the paper contributes,
why it matters for enzyme AI, and any important limitation. Do not copy the
paper abstract.

## Corrections

If a published record has incorrect metadata, open an issue or pull request with
the correction. Maintainers should update the paper record, regenerate the
README and website, and let validation run before merging.

## Project Boundary

- Visitors can submit suggestions, not accepted records.
- The website does not hold a GitHub token.
- Paper suggestions are GitHub issues tied to the submitter account.
- Maintainers control `accepted`, `needs-info`, and `rejected`.
- Localhost, private IP, `.local`, and non-standard-port URLs are rejected.
- Accepted records go through pull requests and validation before reaching
  `main`.
- Subscriber email addresses are not stored in this repository.
