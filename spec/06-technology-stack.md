## 17. Technology stack

### 17.1 Backend

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
- `markdown-it-py`
- pytest and FastAPI TestClient/HTTPX

The initial backend may use synchronous SQLAlchemy sessions. Async database access is not a v1 requirement.

### 17.2 Frontend

Sequencing decision approved by Jack (2026-09-20): retain the frontend framework
migration target below, but defer it until the core backend workflow and
evaluation capabilities are complete. Schedule its concrete slice at a later
review rather than assigning it to an active week now.

Until then, use plain HTML, CSS, and JavaScript in `frontend/`, served by FastAPI
on the same origin. Add the UI controls and result displays needed for each
backend milestone, and fix usability bugs; framework migration is not a
prerequisite for those milestones. No Node build step is required in this phase.

- Node.js 24 LTS baseline
- pnpm with committed lockfile
- current stable Next.js release at initialization time
- React 19
- TypeScript 5+
- App Router
- Vitest
- React Testing Library
- Playwright
