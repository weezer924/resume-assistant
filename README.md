# Evidence-Backed Resume Assistant

A local-first Python application for turning career documents into reviewable
facts, with each statement linked to its original source. The goal is to tailor
resumes to job descriptions without inventing experience.

**Working today:** Markdown import → structured fact extraction → human review.
Job analysis is in progress; retrieval and resume-edit generation are planned.

## Demo

*Recording coming soon: import a synthetic resume, inspect extracted claims and
source quotes, then confirm, edit, and reject individual facts.*

<!-- Replace the recording notice with the GitHub-hosted video URL when available. -->

Try the same workflow locally with the included
[synthetic Japanese resume](tests/fixtures/sample_resume.md).

## What works today

- Import UTF-8 Markdown and persist the original document and ordered source
  sections together in SQLite.
- Extract multiple candidate facts from a selected section using the OpenAI
  Responses API and Pydantic structured output.
- Check that each evidence quote occurs in the saved source before storing
  pending candidates. Record the model, prompt version, output or error, and
  execution timestamps for extraction attempts.
- Confirm, edit, or reject each fact in a browser UI. Edits return the same fact
  to pending while preserving its original claim, source quote, and Run link.
- Reload the current browser tab to recover persisted sources and review states.

Job-description saving is available through `POST /jobs`. Requirement extraction
and quote checking exist at the service layer, but requirement persistence and
the connected API/UI workflow are not yet complete.

## Design

```text
Markdown → saved source sections → model proposes claims + quotes
                                      ↓
                              application checks quotes
                                      ↓
                            pending facts → human review
```

The model proposes content; Python owns IDs, provenance, validation, and review
state. An exact quote match establishes that the excerpt exists, not that it
supports the entire claim—human review remains necessary.

The stack is **Python 3.12+, FastAPI, Pydantic, SQLite, and the OpenAI SDK**, with
plain HTML/CSS/JavaScript served by FastAPI. Thin routes call services and a
SQLite store; tests substitute temporary databases and stub model calls.

The backend is owner-written Python practice, with AI assistance for explanation
and review; the frontend is AI-assisted. See the
[collaboration protocol](spec/08-milestones-acceptance-criteria.md#22-learning-and-collaboration-protocol).

## Run locally

Prerequisites: Python 3.12+, `uv`, `make`, and an OpenAI API key with access to the
configured model (`gpt-5-mini` in [app/dependencies.py](app/dependencies.py)).

```sh
git clone https://github.com/weezer924/resume-assistant.git
cd resume-assistant
uv sync
```

Create a `.env` file in the repository root:

```dotenv
OPENAI_API_KEY=your-api-key
```

Start with a separate demo database:

```sh
RESUME_ASSISTANT_DB_PATH=database/demo.db make dev
```

Open [the review UI](http://127.0.0.1:8000/) or
[interactive API docs](http://127.0.0.1:8000/docs). No frontend build is needed.
Reuse the same database path to keep your data; use a fresh path if an older
checkout created an incompatible schema.

1. Upload `tests/fixtures/sample_resume.md` using **Import document**.
2. Select a source section and click **Extract facts**.
3. Compare each claim with its evidence quote and source text.
4. **Confirm** a supported claim; **Edit** it and observe the return to pending.
   **Reject** a candidate you do not want to use.
5. Reload the same tab to inspect the persisted review state.

Extraction makes a real API call and incurs usage charges. Results can vary.
Documents and review records live locally, but the selected section is sent to
OpenAI during extraction; requests use `store=False`. This is not an offline app.
Use synthetic data for public demos. `.env`, `database/`, and `private/` are
ignored by Git.

To remove demo data, stop the server and delete `database/demo.db` and any
`database/demo.db-*` sidecar files. Clear the tab's session storage or close the
tab to discard its remembered document selection.

## Validation and limits

```sh
make lint                  # Ruff and basedpyright
uv run ruff format --check .
make test                  # pytest; no API key needed
```

Tests cover persistence, quote validation, review transitions, and API behavior
using stub extractors. They do not establish real-model accuracy; a fixed-case
model evaluation and prompt comparison are planned.

- Single-user, local development app; no authentication or public deployment.
- Markdown only; no PDF/DOCX import or exported resume generation.
- No completed job-to-evidence retrieval or resume-suggestion workflow yet.
- Repeated extraction can add duplicate candidates. There is no historical
  document picker or supported migration workflow for older database schemas.

## Roadmap and specifications

Next: finish job analysis and confirmed-only reads, add one retrieval baseline,
then evidence-backed Japanese suggestions and a fixed-case evaluation. Advanced
retrieval comparisons and Agent frameworks are deferred.

See [milestones and approved release scope](spec/08-milestones-acceptance-criteria.md),
[product foundations](spec/01-product-foundations.md),
[data model](spec/02-data-model.md),
[pipeline invariants](spec/03-domain-invariants-pipeline.md), and
[design decisions](spec/adr/).
