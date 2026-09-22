# AGENTS.md

Guidance for coding agents working in this repository. Claude Code reads this file through the `CLAUDE.md` symlink.

## Commands

`Makefile` is the source of truth: `make lint` (ruff + basedpyright), `make test` (pytest), `make fix-ruff` (autofix + format), `make dev` / `make debug` (API with `.env` loaded). CI (`.github/workflows/ci.yml`) runs `ruff format --check`, `make lint`, `make test` on every push; a local `.git/hooks/pre-commit` runs the same checks. Run a single test with `uv run pytest tests/test_<module>.py::test_<behavior>`.

Tests need no `OPENAI_API_KEY`; only `make dev` / `make debug` do (gitignored `.env`).

## Specification gate

The reduced first-release scope is approved in [milestones](spec/08-milestones-acceptance-criteria.md), section 24. Use its stages, time budget, and deferred boundaries for planning. The [Week 3 alignment](spec/adr/week3-model-alignment.md) governs Fact review semantics; historical future-field plans do not expand release scope.

## Specification index and development workflow

Before planning or implementing a slice, read these three sources in order:

1. [Product foundations](spec/01-product-foundations.md): product promise, user boundaries, and portfolio goal.
2. [Milestones and acceptance criteria](spec/08-milestones-acceptance-criteria.md): the current week's deliverables, acceptance criteria, non-goals, and learning protocol.
3. [Data model](spec/02-data-model.md) and [Domain invariants and fixed pipeline](spec/03-domain-invariants-pipeline.md): relationships, provenance, invariants, and stage responsibilities. For Week 3 fields, review transitions, migrations, or UI planning, also read the approved [field and lifecycle alignment](spec/adr/week3-model-alignment.md).

Consult these references for the relevant task:

- [AI and evaluation](spec/04-ai-and-evaluation.md): prompts, retrieval, generation, and evaluation.
- [Application boundary](spec/05-application-boundary-and-technical-shape.md): UI, inputs, and privacy.
- [Technology stack](spec/06-technology-stack.md): technology choices.
- [Repository layout](spec/07-repository-layout.md): directory responsibility boundaries.
- [Evidence Agent ADR](spec/adr/ADR-0001-langgraph-first-for-evidence-agent.md): Agent framework decisions.

For each slice, state the agreed behavior, final responsibility boundary, finite test checklist, and affected interfaces before coding. Use TDD: one behavior test, confirm the expected failure, then minimal implementation. Jack writes all backend code, including CRUD, persistence, API routes, and the AI pipeline. Explain, give isolated examples when requested, and review; supply backend implementation only on explicit request. The assistant may implement UI and frontend work. Follow milestones §22 for the learning protocol. Use fixed cases to evaluate model quality separately from mocked tests.

Compare current code with both the week's scope and the applicable model alignment. Identify planned interface/data changes before implementation so temporary shortcuts do not create avoidable rework. Distinguish completed behavior, deferred fields, and proposed simplifications. Completion is measured against the agreed weekly scope; do not reopen completed weeks to implement every field in the full target model or repeatedly add last-minute tests.

Explicit user decisions override earlier proposals. Apply approved alignment decisions within their scope; other unresolved spec conflicts must be surfaced before dependent work. Keep weekly and detailed specs synchronized when scope changes are authorized. A suggestion alone does not remove an existing requirement. Week 3 retains a connected import, extraction, and confirm/edit/reject UI, as recorded in the alignment document.

## Architecture

Local-first, single-user FastAPI app. SQLite stores original documents, immutable
source spans, reviewable facts, and extraction Runs. Thin routes in `app/routes/`
call `Facts` in `app/services/facts.py` and `SqliteStore` in `app/database.py`.
Extraction validates quotes against saved spans and persists multiple pending
candidates. Confirm/edit/reject update the same Fact ID. Review cannot change
source evidence, so confirmation does not repeat quote validation. See
[the data model](spec/02-data-model.md) for fields and lifecycle rules.

Dependencies are injected in `app/dependencies.py`:

- `SqliteStore(db_path)` (`app/database.py`) owns schema creation and all reads/writes; `get_store` binds it to `database/resume_assistant.db`.
- `FactAIExtractor(client, model)` (`app/services/fact_extraction.py`) owns the model call and passes `store=False`. `app/dependencies.py` supplies the shared model/prompt configuration used by extraction and Run records. `Facts` accepts any `async` callable `SourceSpan -> ModelFactsOutput`.

Tests replace both: `tests/test_facts.py` uses a `tmp_path` sqlite file and a stub extractor; `tests/test_documents.py` overrides `get_store` through `app.dependency_overrides`.

`app/schema.py` holds shared types: `SourceSpan` (`TypedDict`, fields `section`/`level`/`body`/`sequence` for the implemented subset of spec §6.3) and Pydantic models for API and model I/O. Route handlers stay thin; logic lives in `app/services/` and `app/database.py`.

## Privacy

`database/` and `private/` contain real resume data and are gitignored; demos and fixtures use synthetic data only. Before pushing, confirm `.env`, database files, private resumes, and model outputs are absent from `git status`.

## Commits & PRs

Short, imperative, single-purpose commits (`add ruff and basedpyright`). PRs explain the user-visible change, link the issue or spec section, list verification commands, and include sanitized request/response examples for API changes.
