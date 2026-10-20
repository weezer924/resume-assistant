# Evidence-Backed Resume Assistant

A local-first Python application for turning career documents into reviewable facts, with each statement linked to its original source.

For one job description, the app proposes resume wording where every sentence cites a confirmed fact, and names the requirements it has no evidence for instead of filling them in. The starting point is always the JD's requirements.

## Demo

*import a synthetic resume, inspect extracted claims and source quotes, then confirm, edit, and reject individual facts.*

### Get Source Span from MD document
https://github.com/user-attachments/assets/24abc584-6542-4440-8d9e-6f7951d5a598


### Here is the Output for extracted from source span with LLM (OpenAI API)
https://github.com/user-attachments/assets/2776ecdb-5d39-4265-a2b2-c92cda8183c0

### Here is the Job Extra UI with LLM (OpenAI API)
<img width="1515" height="986" alt="Image" src="https://github.com/user-attachments/assets/9adc7dda-26d8-4051-b2c5-af12f3a290a6" />

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
- Paste a job description, extract requirements that carry an explicit
  required/preferred label, and inspect them in the same UI. Each requirement
  quotes the JD verbatim; unlabeled requirements are omitted rather than guessed.
- Read only confirmed facts for downstream use; pending and rejected facts
  never reach retrieval.

## Design

```text
          tests/fixtures/sample_resume.md          job-description text (tests/fixtures/sample_jd.md)
                        │                                       │
            split into source sections              LLM extracts requirements
                        │                            (verbatim quote, required /
            LLM proposes claims + quotes             preferred label only)
                        │                                       │
            app checks each quote exists                app checks each quote
                        │                                       │
            pending facts → human review                 requirements
            confirm / edit / reject                             │
                        │                                       │
                 confirmed facts  ◄──── embed & rank ───────────┘
                        │        (one vector per confirmed fact,
                        │         cosine Top-5 per requirement,
                        │         confirmation re-checked on read)
                        ▼
            retrieval candidates (ids, scores, ranks)
                        │
                        ▼
            LLM writes Japanese suggestions; every factual sentence
            cites a fact id; requirements with no evidence are listed
            as gaps, not filled in
                        │
                        ▼
            app validates every cited id exists and is still confirmed
                        │
                        ▼
            fixed-case evaluation: Recall@K, hard negatives,
            prompt A/B with inputs and model held fixed
```

| Stage | Status |
| --- | --- |
| Resume import, fact extraction, human review | Done (Weeks 1–3) |
| JD import, requirement extraction, confirmed-only reads | Done (Week 4) |
| Embedding retrieval, Top-K, fixed cases, Recall@K | **In progress (Week 5)** — tables, Run records and fixed cases exist; embedding, ranking and the evaluation run are being written |
| Evidence-backed suggestions with citation checks and gap display | Not started (Week 6) |
| Fixed-case evaluation report and prompt comparison | Not started (Week 7) |
| Setup verification, demo, release notes | Not started (Week 8) |

The model proposes content; Python owns IDs, provenance, validation, and review state. An exact quote match establishes that the excerpt exists, not that it supports the entire claim—human review remains necessary.

The stack is **Python 3.12+, FastAPI, Pydantic, SQLite, and the OpenAI SDK**, with plain HTML/CSS/JavaScript served by FastAPI. Thin routes call services and a SQLite store; tests substitute temporary databases and stub model calls.

The backend is myself-written Python, with AI assistance for review; the frontend is AI-assisted. See the
[collaboration protocol](spec/08-milestones-acceptance-criteria.md#22-learning-and-collaboration-protocol).

## Run locally

Prerequisites: Python 3.12+, `uv`, `make`, and an OpenAI API key with access to the configured model (`gpt-5-mini` in [app/dependencies.py](app/dependencies.py)).

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

Open [the review UI](http://127.0.0.1:8000/) Reuse the same database path to keep your data;

1. Upload `tests/fixtures/sample_resume.md` using **Import document**.
2. Select a source section and click **Extract facts**.
3. Compare each claim with its evidence quote and source text.
4. **Confirm** a supported claim; **Edit** it and observe the return to pending.
   **Reject** a candidate you do not want to use.
5. Reload the same tab to inspect the persisted review state.

## Validation and limits

```sh
make lint                  # Ruff and basedpyright
uv run ruff format --check .
make test                  # pytest; no API key needed
```

Tests cover persistence, quote validation, review transitions, and API behavior using stub extractors and embedders. They do not establish real-model quality; 
that is measured separately by the fixed cases in `app/evaluation/` (`tests/fixtures/retrieval_cases.json`), which run against the real model and report Recall@K plus hard-negative and no-evidence behaviour.
