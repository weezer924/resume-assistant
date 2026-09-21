## 17. Technology stack

### 17.1 Backend

- Python with `uv`, `pyproject.toml`, and committed `uv.lock`
- FastAPI and Pydantic
- Official OpenAI Python SDK and Responses API
- SQLite through the existing `sqlite3` store
- pytest and FastAPI TestClient

Select the retrieval implementation when the baseline slice begins. LanceDB
remains an option for a local vector index. An ORM, migration framework, or
parser replacement is not required for this release.

### 17.2 Frontend

Plain HTML, CSS, and JavaScript in `frontend/`, served by FastAPI on the same
origin. No Node build step is required.

Next.js, React, TypeScript, and their test tooling remain deferred migration
candidates after the first release. LangGraph is scoped to a future Evidence
Agent; LangChain is not a delivery target.
