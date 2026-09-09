##  Technology stack

### 1 Backend

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

### 2 Frontend

- Node.js 24 LTS baseline
- pnpm with committed lockfile
- current stable Next.js release at initialization time
- React 19
- TypeScript 5+
- App Router
- Vitest
- React Testing Library
- Playwright