# AGENTS.md

Guidance for coding agents working in this repository. Claude Code reads this file through the `CLAUDE.md` symlink.

## Commands

- `uv sync` — install Python 3.12 dependencies from `uv.lock`, including the dev group.
- `uv run fastapi dev app/main.py` — start the local API with reload.
- `uv run ruff check .` — lint; `uv run ruff format .` — format (`--check` to verify only).
- `uv run basedpyright` — static type checking.
- When adding one: pytest is not in the dev dependencies — add it first, put tests under `tests/test_<module>.py`, run a single test with `uv run pytest tests/test_<module>.py::test_<behavior>`. Use FastAPI `TestClient`/HTTPX for routes and fixed doubles for OpenAI calls.

Fact extraction needs `OPENAI_API_KEY` in the gitignored `.env`.

## Specification gate

The spec (linked in reading order from `README.md`, approval checklist in `spec/05-delivery-learning-and-approval.md`) is **Draft for review**. Implementation beyond explicitly requested exercises waits until it is marked **Approved**. Keep Fact, Evidence, Claim, privacy, and bounded-agent behavior aligned with the relevant spec section.

## Architecture

Local-first, single-user FastAPI app. Product promise: every factual resume claim is backed by confirmed evidence with preserved provenance; missing evidence surfaces instead of being fabricated. The code currently implements one slice of the fixed pipeline:

1. `POST /documents/import` (`app/routes/documents.py`) accepts a markdown upload and persists it via `app/database.py` (raw sqlite3, `database/resume_assistant.db`).
2. `app/services/markdown.py` splits the document into heading-delimited `SourceSpan`s, each with a 1-based `sequence` — this sequence is the provenance link stored alongside every fact.
3. `app/services/fact_extraction.py` calls the OpenAI Responses API (`client.responses.parse` with `text_format=FactDraft` for structured output) to draft one claim + evidence quote from the selected span.
4. Back in the route, a deterministic check verifies `evidence_quote` appears verbatim in the span; mismatch → 422. Safety checks like this live in application code, never only in the prompt — the model is not trusted to enforce them.
5. The draft is only returned, never auto-saved as a fact. Human confirmation is a separate call: `POST /fact/` (`app/routes/fact.py`) persists the confirmed draft to the `facts` table.

Layering: route handlers stay thin; parsing/extraction/persistence live in `app/services/` and `app/database.py`. `app/schema.py` holds shared types — `TypedDict` for internal span structures, Pydantic models for API and model I/O.

## Privacy

`database/` and `private/` contain real resume data and are gitignored; demos and fixtures use synthetic data only. Before pushing, confirm `.env`, database files, private resumes, and model outputs are absent from `git status`.

## Commits & PRs

Short, imperative, single-purpose commits (`add ruff and basedpyright`). PRs explain the user-visible change, link the issue or spec section, list verification commands, and include sanitized request/response examples for API changes.
