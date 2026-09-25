# Local review MVP

Plain HTML/CSS/JavaScript, served by FastAPI. No frontend build step or package
installation is needed. `index.html` defines the page, `style.css` the layout,
and `app.js` the browser interactions. Business rules remain in `app/services/`;
HTTP adapters remain in `app/routes/`.

## Run

From the repository root, with the existing `.env` containing `OPENAI_API_KEY`:

```sh
RESUME_ASSISTANT_DB_PATH=database/week3-ui.db make dev
```

Open http://127.0.0.1:8000/ . This separate database starts empty and is gitignored.
The existing `database/resume_assistant.db` is not migrated or deleted. Reuse the
same new path on later starts to retain your imported data. Running without the
variable uses the default database. Older schemas may be incompatible; use a
fresh demo path instead of overwriting existing data.

Upload a Markdown document, select a source section, extract, inspect the quote,
confirm, edit, and reject individual facts. Watch the same Fact ID change from
pending to confirmed and back to pending. Extraction calls OpenAI with the selected source span; it is not
mocked in normal operation. Use synthetic fixtures for demonstrations.

Only the current document ID is remembered in sessionStorage. Reloading the same
browser tab fetches its persisted spans and facts. Closing the tab can lose the
selection, but does not delete SQLite data. A historical document picker
and job analysis are deferred. Rejection is available for individual facts.
No raw source text is inserted as HTML.

## API connections

- `POST /documents/import`: multipart Markdown upload.
- `GET /documents/{document_id}/review`: persisted spans and candidates.
- `POST /documents/{document_id}/spans/{sequence}/facts`:
  extract and save pending candidates.
- `POST /fact/` with `{"fact_id": 1}`: confirm the existing candidate.
- `PATCH /facts/1` with `{"claim": "Updated synthetic statement"}`: edit and return
  to pending without changing the original claim or evidence.
- `POST /facts/1/reject`: reject the existing candidate. Edit it back to pending
  before confirming again.

## Validation

`tests/test_review_api.py` covers the connected HTTP flow using a temporary SQLite
database and stub extractor. Browser smoke verification also covers import,
extraction, confirmation, edit, reload, and a narrow-screen layout. These checks
do not evaluate the real model's output quality.
