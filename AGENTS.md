# AGENTS.md

Guidance for coding agents working in this repository. Claude Code reads this file through the `CLAUDE.md` symlink.

## Commands

`Makefile` is the source of truth: `make lint` (ruff + basedpyright), `make test` (pytest), `make fix-ruff` (autofix + format), `make run` / `make dev` / `make debug` (API with `.env` loaded). CI (`.github/workflows/ci.yml`) runs `ruff format --check`, `make lint`, `make test` on every push; a local `.git/hooks/pre-commit` runs the same checks. Run a single test with `uv run pytest tests/test_<module>.py::test_<behavior>`.

Tests need no `OPENAI_API_KEY`; only `make run` / `make dev` do (gitignored `.env`).

## Specification gate

The spec (linked in reading order from `README.md`, approval checklist in `spec/05-delivery-learning-and-approval.md`) is **Draft for review**. Implementation beyond explicitly requested exercises waits until it is marked **Approved**. Keep Fact, Evidence, Claim, privacy, and bounded-agent behavior aligned with the relevant spec section.

## Architecture

Local-first, single-user FastAPI app. Product promise: every factual resume claim is backed by confirmed evidence with preserved provenance; missing evidence surfaces instead of being fabricated. The code implements the first three stages of the fixed pipeline (spec §8.1), each as its own HTTP call:

1. `POST /documents/import` (`app/routes/documents.py`) persists the markdown upload and returns its `SourceSpan`s. `app/services/markdown.py` splits on headings; text before the first heading becomes a span with `section=""`, `level=0`. Each span's 1-based `sequence` is the provenance link stored with every fact.
2. `POST /documents/{document_id}/spans/{sequence}/draft` calls `Facts.extract` (`app/services/facts.py`), which locates the span, asks the extractor for a `ModelFactOutput`, verifies `evidence_quote` appears verbatim in the span, and returns a `FactDraft`. The draft is never auto-saved.
3. `POST /fact/` (`app/routes/fact.py`) calls `Facts.confirm`, which re-runs the same span lookup and verbatim check before persisting.

`Facts` owns the invariants: the verbatim check and span lookup run on both paths, and `source_sequence` comes from the located span, never from the model. Deterministic checks live in application code; the model is not trusted to enforce them. Failures raise `SourceSpanNotFound` (404) and `EvidenceNotInSourceSpan` (422), translated by handlers in `app/main.py`.

Dependencies are injected in `app/dependencies.py`:

- `SqliteFactStore(db_path)` (`app/database.py`) owns schema creation and all reads/writes; `get_store` binds it to `database/resume_assistant.db`.
- `OpenAIExtractor(client, model)` (`app/services/fact_extraction.py`) is the only place that knows the model name and passes `store=False`. `Facts` accepts any `async` callable `SourceSpan -> ModelFactOutput`.

Tests replace both: `tests/test_facts.py` uses a `tmp_path` sqlite file and a stub extractor; `tests/test_documents.py` overrides `get_store` through `app.dependency_overrides`.

`app/schema.py` holds shared types: `SourceSpan` (`TypedDict`, fields `section`/`level`/`body`/`sequence` per spec §6.3) and Pydantic models for API and model I/O. Route handlers stay thin; logic lives in `app/services/` and `app/database.py`.

## Privacy

`database/` and `private/` contain real resume data and are gitignored; demos and fixtures use synthetic data only. Before pushing, confirm `.env`, database files, private resumes, and model outputs are absent from `git status`.

## Commits & PRs

Short, imperative, single-purpose commits (`add ruff and basedpyright`). PRs explain the user-visible change, link the issue or spec section, list verification commands, and include sanitized request/response examples for API changes.
