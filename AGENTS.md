# AGENTS.md

Guidance for coding agents working in this repository. Claude Code reads this file through the `CLAUDE.md` symlink.

## Commands

`Makefile` is the source of truth: `make lint` (ruff + basedpyright), `make test` (pytest), `make fix-ruff` (autofix + format), `make dev` / `make debug` (API with `.env` loaded). CI (`.github/workflows/ci.yml`) runs `ruff format --check`, `make lint`, `make test` on every push; a local `.git/hooks/pre-commit` runs the same checks. Run a single test with `uv run pytest tests/test_<module>.py::test_<behavior>`.

Tests need no `OPENAI_API_KEY`; only `make dev` / `make debug` do (gitignored `.env`).

## Specification gate

The overall spec remains **Draft for review**; the approval checklist is in [milestones and acceptance criteria](spec/08-milestones-acceptance-criteria.md), section 24. Implementation beyond explicitly requested exercises waits for approval. The approved [Week 3 model alignment](spec/adr/week3-model-alignment.md) governs its stated decisions, without implying approval of the entire spec.

## Specification index and development workflow

Before planning or implementing a slice, read these three sources in order:

1. [Product foundations](spec/01-product-foundations.md): product promise, user boundaries, and portfolio goal.
2. [Milestones and acceptance criteria](spec/08-milestones-acceptance-criteria.md): the current week's deliverables, acceptance criteria, non-goals, and learning protocol.
3. [Data model](spec/02-data-model.md) and [Domain invariants and fixed pipeline](spec/03-domain-invariants-pipeline.md): relationships, provenance, invariants, and stage responsibilities. For Week 3 fields, review transitions, migrations, or UI planning, also read the approved [field and lifecycle alignment](spec/adr/week3-model-alignment.md).

Consult these references for the relevant task:

- [AI and evaluation](spec/04-ai-and-evaluation.md): prompts, retrieval, generation, judges, and evaluation.
- [Application boundary](spec/05-application-boundary-and-technical-shape.md): UI, inputs, and privacy.
- [Technology stack](spec/06-technology-stack.md): technology choices.
- [Repository layout](spec/07-repository-layout.md): directory responsibility boundaries.
- [Evidence Agent ADR](spec/adr/ADR-0001-langgraph-first-for-evidence-agent.md): Agent framework decisions.

For each slice, state the agreed behavior, final responsibility boundary, finite test checklist, and affected interfaces before coding. Use TDD: one behavior test, confirm the expected failure, then minimal implementation. Jack writes core code; provide hints and isolated examples, and supply a full implementation only when explicitly requested. Use fixed cases to evaluate model quality separately from mocked tests.

Compare current code with both the week's scope and the applicable model alignment. Identify planned interface/data changes before implementation so temporary shortcuts do not create avoidable rework. Distinguish completed behavior, deferred fields, and proposed simplifications. Completion is measured against the agreed weekly scope; do not reopen completed weeks to implement every field in the full target model or repeatedly add last-minute tests.

Explicit user decisions override earlier proposals. Apply approved alignment decisions within their scope; other unresolved spec conflicts must be surfaced before dependent work. Keep weekly and detailed specs synchronized when scope changes are authorized. A suggestion alone does not remove an existing requirement. Week 3 retains a connected import, extraction, and confirm/edit/reject UI, as recorded in the alignment document.

## Architecture

Local-first, single-user FastAPI app. Product promise: every factual resume claim is backed by confirmed evidence with preserved provenance; missing evidence surfaces instead of being fabricated. The code implements the first three stages of the fixed pipeline (spec §8.1), each as its own HTTP call:

1. `POST /documents/import` (`app/routes/documents.py`) parses Markdown and persists the Document and its `SourceSpan`s in one transaction, then returns the spans. `app/services/markdown.py` splits on headings; text before the first heading becomes a span with `section=""`, `level=0`. Each span's 1-based `sequence` is the provenance link stored with every fact.
2. `POST /documents/{document_id}/spans/{sequence}/draft` calls `Facts.extract` (`app/services/facts.py`), which reads the persisted span without reparsing the Document, asks the extractor for a `ModelFactOutput`, verifies `evidence_quote` appears verbatim in the span, and returns a `FactDraft`. Currently the draft is returned without being saved as a Fact; successful and failed extraction Runs are persisted. Week 3 plans pending-candidate persistence; consult the alignment before changing this behavior.
3. `POST /fact/` (`app/routes/fact.py`) calls `Facts.confirm`, which re-runs the same span lookup and verbatim check before persisting.

`Facts` owns the invariants: the verbatim check and span lookup run on both paths, and `source_sequence` comes from the located span, never from the model. Deterministic checks live in application code; the model is not trusted to enforce them. Failures raise `SourceSpanNotFound` (404) and `EvidenceNotInSourceSpan` (422), translated by handlers in `app/main.py`.

Dependencies are injected in `app/dependencies.py`:

- `SqliteFactStore(db_path)` (`app/database.py`) owns schema creation and all reads/writes; `get_store` binds it to `database/resume_assistant.db`.
- `OpenAIExtractor(client, model)` (`app/services/fact_extraction.py`) owns the model call and passes `store=False`. `app/dependencies.py` supplies the shared model/prompt configuration used by extraction and Run records. `Facts` accepts any `async` callable `SourceSpan -> ModelFactOutput`.

Tests replace both: `tests/test_facts.py` uses a `tmp_path` sqlite file and a stub extractor; `tests/test_documents.py` overrides `get_store` through `app.dependency_overrides`.

`app/schema.py` holds shared types: `SourceSpan` (`TypedDict`, fields `section`/`level`/`body`/`sequence` for the implemented subset of spec §6.3) and Pydantic models for API and model I/O. Route handlers stay thin; logic lives in `app/services/` and `app/database.py`.

## Privacy

`database/` and `private/` contain real resume data and are gitignored; demos and fixtures use synthetic data only. Before pushing, confirm `.env`, database files, private resumes, and model outputs are absent from `git status`.

## Commits & PRs

Short, imperative, single-purpose commits (`add ruff and basedpyright`). PRs explain the user-visible change, link the issue or spec section, list verification commands, and include sanitized request/response examples for API changes.
