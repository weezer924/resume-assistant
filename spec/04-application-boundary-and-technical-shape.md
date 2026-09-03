## 14. UI specification

### 14.1 Documents

Responsibilities:

- import supported local files
- show parser status and errors
- display content hash and source sections
- allow local deletion
- never imply that import means facts are trusted

### 14.2 Facts

Responsibilities:

- list pending, confirmed, rejected, and conflicting Facts
- display exact supporting SourceSpans
- allow confirm, edit, and reject
- preserve original extraction and edit history
- show retrieval eligibility

### 14.3 Job

Responsibilities:

- accept pasted job text
- display extracted JobRequirements
- show required versus preferred classification
- allow the user to inspect parsing before generation

### 14.4 Suggestions

Responsibilities:

- display original and proposed content
- show related requirements
- show supporting Evidence IDs and excerpts
- separate supported content, clarification questions, and skill-development suggestions
- support accept, edit, and reject
- prevent unsupported content from appearing as publishable

### 14.5 Run Detail

The fixed pipeline view shows:

- step name and status
- start/end time and latency
- prompt and model version
- input/output schema result
- tokens and estimated cost
- retrieval candidates and scores
- selected Evidence
- checker and judge outputs
- retries, fallbacks, and errors

The Agent timeline shows:

- turn number
- tool name
- structured tool input
- bounded tool result or result summary
- Evidence IDs inspected
- final support status
- structured stop reason
- guardrail or limit events

The UI never displays hidden chain-of-thought.

### 14.6 Evals

Responsibilities:

- select dataset, model role configuration, and prompt version
- compare run summaries
- filter by rule and failure category
- inspect expected behavior, actual output, evidence, and verdict
- show hard gates separately from soft metrics
- link disagreements to human labels

### 14.7 Frontend testing scope

Vitest and React Testing Library cover a small set of critical UI invariants:

- unconfirmed Facts cannot enter generation
- Fact confirm/edit/reject state is rendered correctly
- Evidence details resolve to the correct source
- unsupported requirements are separated from supported Claims
- skill-development suggestions never appear in resume content
- Agent failures display a safe terminal state

Playwright covers two primary mocked-API paths:

1. synthetic import → fact confirmation → job analysis → suggestion → evidence inspection
2. missing requirement evidence → deeper investigation → `NO_EVIDENCE` → separate development suggestion

Frontend testing should consume approximately 10–15% of project effort. Test count or coverage percentage is not itself a success criterion.

## 15. Supported input formats

### 15.1 v1

- DOCX
- Markdown
- UTF-8 or UTF-8-BOM TXT
- pasted job description
- pasted LinkedIn profile text
- relevant LinkedIn export CSV when its schema is explicitly supported
- selected project notes in supported text formats

DOCX parsing must include paragraphs and table cells and retain source coordinates. Markdown is parsed as structured tokens rather than converted to presentation HTML first.

### 15.2 Parsing failure behavior

- Unsupported files are rejected with a clear message.
- Partial parsing is visibly marked and cannot silently become trusted evidence.
- The application offers pasted text as a fallback.
- Parser name and version are recorded.

### 15.3 Post-v1 candidates

- digital-text PDF
- richer LinkedIn export support

Scanned PDF, image OCR, and VLM document understanding are out of scope.

## 16. Privacy, security, and public repository boundary

### 16.1 Local data handling

- Raw personal documents remain local.
- Personal datasets and run artifacts are gitignored.
- Local paths and original filenames are not exported in public reports.
- The application provides deletion of imported local data.
- SQLite and LanceDB files containing personal data are not committed.

### 16.2 OpenAI API boundary

- Parse documents locally before model calls.
- Send only the minimum text required for the current extraction, generation, or judging task.
- Use `store=false` for Responses requests.
- Do not describe `store=false` as absolute zero retention.
- Do not upload the entire personal corpus when selected SourceSpans are sufficient.

### 16.3 Logging

General logs contain IDs, hashes, timings, token usage, statuses, and safe error metadata. They do not duplicate full resume text, personal contact details, API keys, or hidden model reasoning.

### 16.4 Untrusted content

Resume text, LinkedIn text, project notes, job descriptions, and retrieved passages are data, not instructions. Prompt injection attempts must not:

- change confirmation status
- expand Agent tools
- bypass checkers
- reveal prompts or private context
- cause unsupported Claims to be published

### 16.5 Public repository content

Allowed public content:

- application source code
- architecture and specification documents
- synthetic fixtures
- public evaluation dataset
- sanitized evaluation reports
- local setup and demo instructions

Forbidden public content:

- real personal resume or LinkedIn data
- contact details
- company proprietary prompts, code, production samples, or datasets
- OpenAI API keys or other credentials
- Object IDs or logs that can identify real people or business records
- private evaluation outputs

## 17. Explicit non-goals

The 8–10 week release does not include:

- public hosted service
- user registration, OAuth, or multi-user authorization
- Gmail, Google Drive, or LinkedIn account integrations
- automatic website crawling
- scanned-document OCR
- image/VLM document understanding
- digital PDF support unless added after core completion
- autonomous Agent control of the core pipeline
- multi-agent systems
- MCP or A2A integration
- LangChain or LangGraph outside the Evidence Agent
- fine-tuning or model training
- self-improving or Meta Agent behavior
- open-ended autonomous exploration
- automatic job application submission
- full DOCX/PDF resume layout generation
- mobile-specific layout work
- public real-time API use
- conventional data-science model development or feature-engineering claims

## 18. Technology stack

### 18.1 Backend

- CPython 3.12
- `uv`, `pyproject.toml`, and committed `uv.lock`
- FastAPI
- Pydantic v2 and `pydantic-settings`
- official OpenAI Python SDK and Responses API
- LangGraph with `langchain-openai` for the bounded Evidence Agent
- SQLAlchemy 2.x
- Alembic with SQLite batch migrations
- SQLite with foreign keys enabled and strict tables where appropriate
- LanceDB Python in local embedded mode
- `python-docx`
- `markdown-it-py`
- pytest and FastAPI TestClient/HTTPX

The initial backend may use synchronous SQLAlchemy sessions. Async database access is not a v1 requirement.

### 18.2 Frontend

- Node.js 24 LTS baseline
- pnpm with committed lockfile
- current stable Next.js release at initialization time
- React 19
- TypeScript 5+
- App Router
- Vitest
- React Testing Library
- Playwright

### 18.3 Runtime and local development

Docker is not required for v1 because SQLite and LanceDB are local files and both application processes run locally. Docker may be added later only when it solves a verified reproducibility, deployment, or CI problem.

### 18.4 Dependency rules

- Exact dependency versions are locked at project initialization.
- Business logic does not depend directly on model names.
- Framework abstractions must not hide prompt inputs, context, tool calls, usage, or errors from the Run record.
- LangGraph is a v1 dependency scoped to the Evidence Agent. Any further AI framework requires a measured use case and an evaluation comparison before adoption.

## 19. Repository and artifact layout

This section defines responsibility boundaries, not mandatory implementation details.

```text
resume-assistant/
  backend/
    application and evaluation packages
  frontend/
    local web application
  prompts/
    versioned prompt sources and manifest
  database/
    public synthetic fixtures and expected behavior
  reports/
    sanitized, reproducible public reports
  docs/
    architecture, runbook, demo, and decisions
  private/
    local-only gitignored data and outputs
```

The exact code directory structure is chosen during implementation and reviewed against module depth and responsibility, not copied mechanically from this outline.
