import json
import sqlite3
from typing import Literal, cast

from app.schema import (
    Document,
    EmbeddingRun,
    FactDraft,
    Job,
    JobRequirement,
    ModelFactOutput,
    ModelFactRun,
    ModelJobRequirementOutput,
    ModelJobRun,
    RetrievalCandidate,
    RetrievalCandidateDraft,
    SourceSpan,
)


class SqliteStore:
    def __init__(self, db_path: str):
        self.db_path: str = db_path
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as connection:
            _ = connection.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            _ = connection.execute("""
                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id TEXT NOT NULL,
                    claim TEXT NOT NULL,
                    confirmed_at TEXT,
                    evidence_quote TEXT NOT NULL,
                    source_sequence INTEGER NOT NULL,
                    original_claim TEXT NOT NULL,
                    status TEXT NOT NULL CHECK (status IN ('pending', 'confirmed', 'rejected')),
                    extraction_run_id INTEGER,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents(document_id)
                )
            """)

            _ = connection.execute("""
                CREATE TABLE IF NOT EXISTS model_fact_run (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id TEXT NOT NULL,
                    source_sequence INTEGER NOT NULL,
                    model TEXT NOT NULL,
                    prompt_id TEXT NOT NULL,
                    prompt_version TEXT NOT NULL,
                    start_at REAL NOT NULL,
                    completed_at REAL NOT NULL,
                    status TEXT NOT NULL,
                    output TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents(document_id)
                )
            """)

            _ = connection.execute("""
                CREATE TABLE IF NOT EXISTS source_spans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id TEXT NOT NULL,
                    section TEXT NOT NULL,
                    level INTEGER NOT NULL,
                    body TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents(document_id)
                )
            """)

            _ = connection.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    source_text TEXT NOT NULL
                )
            """)

            _ = connection.execute("""
                CREATE TABLE IF NOT EXISTS model_job_run (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    model TEXT NOT NULL,
                    prompt_id TEXT NOT NULL,
                    prompt_version TEXT NOT NULL,
                    start_at REAL NOT NULL,
                    completed_at REAL NOT NULL,
                    status TEXT NOT NULL,
                    output TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (job_id) REFERENCES jobs(id)
                )
            """)

            # confirm 一条 fact ──→ 调 API ──→ embedding_run(fact)  +  fact_embeddings 写一行
            # 检索一条 requirement ─→ 调 API ──→ embedding_run(requirement)，向量只在内存里
            #                                       └─→ 和 fact_embeddings 全表算距离 → Top-K
            _ = connection.execute("""
                CREATE TABLE IF NOT EXISTS embedding_run (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    input_kind TEXT NOT NULL CHECK (input_kind IN ('fact', 'requirement')),
                    input_ref INTEGER NOT NULL,
                    model TEXT NOT NULL,
                    start_at REAL NOT NULL,
                    completed_at REAL NOT NULL,
                    status TEXT NOT NULL,
                    error TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Rebuildable projection of confirmed facts (spec 10.1); one row per fact.
            _ = connection.execute("""
                CREATE TABLE IF NOT EXISTS fact_embeddings (
                    fact_id INTEGER PRIMARY KEY,
                    model TEXT NOT NULL,
                    vector TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (fact_id) REFERENCES facts(id)
                )
            """)

            # for 评测,
            _ = connection.execute("""
                CREATE TABLE IF NOT EXISTS retrieval_candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_requirement_id INTEGER NOT NULL,
                    fact_id INTEGER NOT NULL,
                    method TEXT NOT NULL,
                    score REAL NOT NULL,
                    rank INTEGER NOT NULL,
                    selected INTEGER NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (job_requirement_id) REFERENCES job_requirements(id),
                    FOREIGN KEY (fact_id) REFERENCES facts(id)
                )
            """)

            _ = connection.execute("""
                CREATE TABLE IF NOT EXISTS job_requirements (
                    id INTEGER PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    requirement_text TEXT NOT NULL,
                    normalized_requirement TEXT NOT NULL,
                    category TEXT NOT NULL,
                    required_or_preferred TEXT NOT NULL,
                    years_or_level TEXT
                )
            """)

    def save_document(self, document: Document):
        with sqlite3.connect(self.db_path) as connection:
            _ = connection.execute(
                """
                INSERT INTO documents (document_id, filename, content)
                VALUES (?, ?, ?)
                """,
                (document.document_id, document.filename, document.content),
            )

    def get_document(self, document_id: str) -> Document | None:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                SELECT document_id, filename, content
                FROM documents
                WHERE document_id = ?
                """,
                (document_id,),
            )
            row = cast(tuple[str, str, str] | None, cursor.fetchone())
            if row is None:
                return None
            return Document(document_id=row[0], filename=row[1], content=row[2])

    def get_source_span(self, document_id: str, sequence: int) -> SourceSpan | None:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                SELECT section, level, body, sequence
                FROM source_spans
                WHERE document_id = ? AND sequence = ?
                """,
                (document_id, sequence),
            )
            row = cast(tuple[str, int, str, int] | None, cursor.fetchone())
            if row is None:
                return None
            return {
                "section": row[0],
                "level": row[1],
                "body": row[2],
                "sequence": row[3],
            }

    def get_source_spans(self, document_id: str) -> list[SourceSpan]:
        with sqlite3.connect(self.db_path) as connection:
            rows = cast(
                list[tuple[str, int, str, int]],
                connection.execute(
                    """SELECT section, level, body, sequence FROM source_spans
                    WHERE document_id = ? ORDER BY sequence""",
                    (document_id,),
                ).fetchall(),
            )
            return [
                SourceSpan(section=row[0], level=row[1], body=row[2], sequence=row[3])
                for row in rows
            ]

    def save_source_span(self, document_id: str, source_span: SourceSpan) -> None:
        with sqlite3.connect(self.db_path) as connection:
            _ = connection.execute(
                """
                INSERT INTO source_spans (document_id, section, level, body, sequence)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    document_id,
                    source_span["section"],
                    source_span["level"],
                    source_span["body"],
                    source_span["sequence"],
                ),
            )

    def save_document_with_spans(
        self, document: Document, source_spans: list[SourceSpan]
    ) -> None:
        with sqlite3.connect(self.db_path) as connection:
            _ = connection.execute(
                """
                INSERT INTO documents (document_id, filename, content)
                VALUES (?, ?, ?)
                """,
                (document.document_id, document.filename, document.content),
            )
            for source_span in source_spans:
                _ = connection.execute(
                    """
                    INSERT INTO source_spans (document_id, section, level, body, sequence)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        document.document_id,
                        source_span["section"],
                        source_span["level"],
                        source_span["body"],
                        source_span["sequence"],
                    ),
                )

    def save_fact(
        self,
        document_id: str,
        claim: str,
        evidence_quote: str,
        source_sequence: int,
        extraction_run_id: int,
    ) -> int:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                    INSERT INTO facts (
                        document_id,
                        claim,
                        evidence_quote,
                        original_claim,
                        source_sequence,
                        status,
                        extraction_run_id,
                        confirmed_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document_id,
                    claim,
                    evidence_quote,
                    claim,
                    source_sequence,
                    "pending",
                    extraction_run_id,
                    None,
                ),
            )
            if cursor.lastrowid is None:
                raise ValueError("Failed to insert fact")

            return cursor.lastrowid

    def save_facts(
        self,
        document_id: str,
        facts: list[ModelFactOutput],
        source_sequence: int,
        extraction_run_id: int,
    ) -> list[int]:
        with sqlite3.connect(self.db_path) as connection:
            fact_ids: list[int] = []
            for fact in facts:
                cursor = connection.execute(
                    """
                        INSERT INTO facts (
                            document_id,
                            claim,
                            evidence_quote,
                            original_claim,
                            source_sequence,
                            status,
                            extraction_run_id,
                            confirmed_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        document_id,
                        fact.claim,
                        fact.evidence_quote,
                        fact.claim,
                        source_sequence,
                        "pending",
                        extraction_run_id,
                        None,
                    ),
                )

                if cursor.lastrowid is None:
                    raise RuntimeError("Failed to insert fact")

                fact_ids.append(cursor.lastrowid)

            return fact_ids

    def confirm_fact(self, fact_id: int) -> FactDraft | None:
        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.execute(
                """
                UPDATE facts
                SET status = 'confirmed', confirmed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND status = 'pending'
                RETURNING *
                """,
                (fact_id,),
            )
            row = cast(sqlite3.Row | None, cursor.fetchone())

            if row is None:
                return None
            return FactDraft.model_validate(dict(row))

    def edit_fact(self, fact_id: int, claim: str) -> FactDraft | None:
        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.execute(
                """
                UPDATE facts
                SET claim = ?, status = 'pending', confirmed_at = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                RETURNING *
                """,
                (
                    claim,
                    fact_id,
                ),
            )
            row = cast(sqlite3.Row | None, cursor.fetchone())

            if row is None:
                return None

            return FactDraft.model_validate(dict(row))

    def reject_fact(self, fact_id: int) -> FactDraft | None:
        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.execute(
                """
                UPDATE facts
                SET status = 'rejected', confirmed_at = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND status IN ('pending', 'confirmed')
                RETURNING *
                """,
                (fact_id,),
            )
            row = cast(sqlite3.Row | None, cursor.fetchone())

            if row is None:
                return None

            return FactDraft.model_validate(dict(row))

    def get_facts(self, document_id: str) -> list[FactDraft]:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                SELECT id, document_id, claim, evidence_quote, original_claim, source_sequence, status, extraction_run_id, confirmed_at, created_at, updated_at
                FROM facts
                WHERE document_id = ?
                """,
                (document_id,),
            )
            rows = cast(
                list[
                    tuple[
                        int,  # id: int
                        str,  # document_id: str
                        str,  # claim: str
                        str,  # evidence_quote: str
                        str,  # original_claim: str
                        int,  # source_sequence: int
                        Literal["pending", "confirmed", "rejected"],  # status
                        int | None,  # extraction_run_id: int | None
                        str | None,  # confirmed_at: str | None
                        str,  # created_at: str
                        str,  # updated_at: str
                    ]
                ],
                cursor.fetchall(),
            )
            return [
                FactDraft(
                    id=row[0],
                    document_id=row[1],
                    claim=row[2],
                    evidence_quote=row[3],
                    original_claim=row[4],
                    source_sequence=row[5],
                    status=row[6],
                    extraction_run_id=row[7],
                    confirmed_at=row[8],
                    created_at=row[9],
                    updated_at=row[10],
                )
                for row in rows
            ]

    def get_confirmed_facts(self) -> list[FactDraft]:
        """Facts eligible for retrieval and generation: confirmed only, across all documents."""
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                SELECT id, document_id, claim, evidence_quote, original_claim, source_sequence, status, extraction_run_id, confirmed_at, created_at, updated_at
                FROM facts
                WHERE status = 'confirmed'
                ORDER BY id
                """
            )
            rows = cast(
                list[
                    tuple[
                        int,  # id: int
                        str,  # document_id: str
                        str,  # claim: str
                        str,  # evidence_quote: str
                        str,  # original_claim: str
                        int,  # source_sequence: int
                        Literal["pending", "confirmed", "rejected"],  # status
                        int | None,  # extraction_run_id: int | None
                        str | None,  # confirmed_at: str | None
                        str,  # created_at: str
                        str,  # updated_at: str
                    ]
                ],
                cursor.fetchall(),
            )
            return [
                FactDraft(
                    id=row[0],
                    document_id=row[1],
                    claim=row[2],
                    evidence_quote=row[3],
                    original_claim=row[4],
                    source_sequence=row[5],
                    status=row[6],
                    extraction_run_id=row[7],
                    confirmed_at=row[8],
                    created_at=row[9],
                    updated_at=row[10],
                )
                for row in rows
            ]

    def get_fact(self, fact_id: int) -> FactDraft | None:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                SELECT id, document_id, claim, evidence_quote,original_claim, source_sequence, status,extraction_run_id,confirmed_at, created_at, updated_at
                FROM facts
                WHERE id = ?
                """,
                (fact_id,),
            )
            row = cast(
                tuple[
                    int,  # id: int
                    str,  # document_id: str
                    str,  # claim: str
                    str,  # evidence_quote: str
                    str,  # original_claim: str
                    int,  # source_sequence: int
                    Literal["pending", "confirmed", "rejected"],  # status
                    int | None,  # extraction_run_id: int | None
                    str | None,  # confirmed_at: str | None
                    str,  # created_at: str
                    str,  # updated_at: str
                ]
                | None,
                cursor.fetchone(),
            )
        if row is None:
            return None

        return FactDraft(
            id=row[0],
            document_id=row[1],
            claim=row[2],
            evidence_quote=row[3],
            original_claim=row[4],
            source_sequence=row[5],
            status=row[6],
            extraction_run_id=row[7],
            confirmed_at=row[8],
            created_at=row[9],
            updated_at=row[10],
        )

    def save_model_fact_run(self, model_fact_run: ModelFactRun) -> int:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO model_fact_run (
                    document_id,
                    source_sequence,
                    model,
                    prompt_id,
                    prompt_version,
                    start_at,
                    completed_at,
                    status,
                    output,
                    error
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    model_fact_run.document_id,
                    model_fact_run.source_sequence,
                    model_fact_run.model,
                    model_fact_run.prompt_id,
                    model_fact_run.prompt_version,
                    model_fact_run.start_at,
                    model_fact_run.completed_at,
                    model_fact_run.status,
                    model_fact_run.output,
                    model_fact_run.error,
                ),
            )

            if cursor.lastrowid is None:
                raise ValueError("Failed to insert model_fact_run")

            return cursor.lastrowid

    def get_model_fact_run(self, run_id: int) -> ModelFactRun | None:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                SELECT document_id, source_sequence, model, prompt_id, prompt_version, start_at, completed_at, status, output, error
                FROM model_fact_run
                WHERE id = ?
                """,
                (run_id,),
            )
            row = cast(
                tuple[str, int, str, str, str, float, float, str, str, str] | None,
                (cursor.fetchone()),
            )
            if row is None:
                return None
            return ModelFactRun(
                document_id=row[0],
                source_sequence=row[1],
                model=row[2],
                prompt_id=row[3],
                prompt_version=row[4],
                start_at=row[5],
                completed_at=row[6],
                status=row[7],
                output=row[8],
                error=row[9],
            )

    def get_model_fact_runs(self, document_id: str) -> list[ModelFactRun]:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                SELECT document_id, source_sequence, model, prompt_id, prompt_version, start_at, completed_at, status, output, error
                FROM model_fact_run
                WHERE document_id = ?
                """,
                (document_id,),
            )
            rows: list[tuple[str, int, str, str, str, float, float, str, str, str]] = (
                cursor.fetchall()
            )
            return [
                ModelFactRun(
                    document_id=row[0],
                    source_sequence=row[1],
                    model=row[2],
                    prompt_id=row[3],
                    prompt_version=row[4],
                    start_at=row[5],
                    completed_at=row[6],
                    status=row[7],
                    output=row[8],
                    error=row[9],
                )
                for row in rows
            ]

    def save_job(self, job: Job) -> None:
        with sqlite3.connect(self.db_path) as connection:
            _ = connection.execute(
                """
                    INSERT INTO jobs (
                        id,
                        source_text
                    )
                    VALUES (?,?)
                """,
                (job.id, job.source_text),
            )

    def get_job(self, job_id: str) -> Job | None:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                SELECT id, source_text
                FROM jobs
                WHERE id = ?
                """,
                (job_id,),
            )

            row = cast(tuple[str, str] | None, cursor.fetchone())

            if row is None:
                return None

            return Job(id=row[0], source_text=row[1])

    def save_job_requirements(
        self,
        job_id: str,
        requirements: list[ModelJobRequirementOutput],
    ) -> list[int]:
        with sqlite3.connect(self.db_path) as connection:
            requirement_ids: list[int] = []
            for requirement in requirements:
                cursor = connection.execute(
                    """
                    INSERT INTO job_requirements (
                        job_id, requirement_text, normalized_requirement, category, required_or_preferred, years_or_level
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        job_id,
                        requirement.requirement_text,
                        requirement.normalized_requirement,
                        requirement.category,
                        requirement.required_or_preferred,
                        requirement.years_or_level,
                    ),
                )

                if cursor.lastrowid is None:
                    raise RuntimeError("Failed to insert requirement")

                requirement_ids.append(cursor.lastrowid)

            return requirement_ids

    def get_job_requirements(self, job_id: str) -> list[JobRequirement]:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                SELECT id, job_id, requirement_text, normalized_requirement, category, required_or_preferred, years_or_level
                FROM job_requirements
                WHERE job_id = ?
                ORDER BY id
                """,
                (job_id,),
            )

            rows = cast(
                list[
                    tuple[
                        int,  # id: int
                        str,  # job_id: str
                        str,  # requirement_text: str
                        str,  # normalized_requirement: str
                        str,  # category: str
                        Literal["required", "preferred"],  # required_or_preferred: str
                        str | None,  # years_or_level: str | None
                    ]
                ],
                cursor.fetchall(),
            )

            return [
                JobRequirement(
                    id=row[0],
                    job_id=row[1],
                    requirement_text=row[2],
                    normalized_requirement=row[3],
                    category=row[4],
                    required_or_preferred=row[5],
                    years_or_level=row[6],
                )
                for row in rows
            ]

    # --- Week 5 plumbing: Runs, embedding projection, retrieval candidates ---

    def save_model_job_run(self, model_job_run: ModelJobRun) -> int:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO model_job_run (
                    job_id, model, prompt_id, prompt_version,
                    start_at, completed_at, status, output, error
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    model_job_run.job_id,
                    model_job_run.model,
                    model_job_run.prompt_id,
                    model_job_run.prompt_version,
                    model_job_run.start_at,
                    model_job_run.completed_at,
                    model_job_run.status,
                    model_job_run.output,
                    model_job_run.error,
                ),
            )
            if cursor.lastrowid is None:
                raise RuntimeError("Failed to insert model job run")
            return cursor.lastrowid

    def get_model_job_runs(self, job_id: str) -> list[ModelJobRun]:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                SELECT job_id, model, prompt_id, prompt_version, start_at, completed_at, status, output, error
                FROM model_job_run
                WHERE job_id = ?
                ORDER BY id
                """,
                (job_id,),
            )
            rows = cast(
                list[
                    tuple[str, str, str, str, float, float, str, str | None, str | None]
                ],
                cursor.fetchall(),
            )
            return [
                ModelJobRun(
                    job_id=row[0],
                    model=row[1],
                    prompt_id=row[2],
                    prompt_version=row[3],
                    start_at=row[4],
                    completed_at=row[5],
                    status=row[6],
                    output=row[7],
                    error=row[8],
                )
                for row in rows
            ]

    def save_embedding_run(self, embedding_run: EmbeddingRun) -> int:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO embedding_run (
                    input_kind, input_ref, model, start_at, completed_at, status, error
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    embedding_run.input_kind,
                    embedding_run.input_ref,
                    embedding_run.model,
                    embedding_run.start_at,
                    embedding_run.completed_at,
                    embedding_run.status,
                    embedding_run.error,
                ),
            )
            if cursor.lastrowid is None:
                raise RuntimeError("Failed to insert embedding run")
            return cursor.lastrowid

    def get_embedding_runs(
        self, input_kind: Literal["fact", "requirement"], input_ref: int
    ) -> list[EmbeddingRun]:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                SELECT input_kind, input_ref, model, start_at, completed_at, status, error
                FROM embedding_run
                WHERE input_kind = ? AND input_ref = ?
                ORDER BY id
                """,
                (input_kind, input_ref),
            )
            rows = cast(
                list[
                    tuple[
                        Literal["fact", "requirement"],
                        int,
                        str,
                        float,
                        float,
                        str,
                        str | None,
                    ]
                ],
                cursor.fetchall(),
            )
            return [
                EmbeddingRun(
                    input_kind=row[0],
                    input_ref=row[1],
                    model=row[2],
                    start_at=row[3],
                    completed_at=row[4],
                    status=row[5],
                    error=row[6],
                )
                for row in rows
            ]

    def upsert_fact_embedding(
        self, fact_id: int, model: str, vector: list[float]
    ) -> None:
        with sqlite3.connect(self.db_path) as connection:
            _ = connection.execute(
                """
                INSERT INTO fact_embeddings (fact_id, model, vector)
                VALUES (?, ?, ?)
                ON CONFLICT(fact_id) DO UPDATE SET
                    model = excluded.model,
                    vector = excluded.vector,
                    created_at = CURRENT_TIMESTAMP
                """,
                (fact_id, model, json.dumps(vector)),
            )

    def delete_fact_embedding(self, fact_id: int) -> None:
        with sqlite3.connect(self.db_path) as connection:
            _ = connection.execute(
                "DELETE FROM fact_embeddings WHERE fact_id = ?", (fact_id,)
            )

    def get_fact_embeddings(self, model: str) -> list[tuple[int, list[float]]]:
        """All stored vectors for one model, in fact id order. Callers must still
        check each fact's current status; this table is a projection, not truth."""
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                SELECT fact_id, vector
                FROM fact_embeddings
                WHERE model = ?
                ORDER BY fact_id
                """,
                (model,),
            )
            rows = cast(list[tuple[int, str]], cursor.fetchall())
            return [
                (fact_id, cast(list[float], json.loads(vector)))
                for fact_id, vector in rows
            ]

    def save_retrieval_candidates(
        self, candidates: list[RetrievalCandidateDraft]
    ) -> list[int]:
        with sqlite3.connect(self.db_path) as connection:
            ids: list[int] = []
            for candidate in candidates:
                cursor = connection.execute(
                    """
                    INSERT INTO retrieval_candidates (
                        job_requirement_id, fact_id, method, score, rank, selected
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        candidate.job_requirement_id,
                        candidate.fact_id,
                        candidate.method,
                        candidate.score,
                        candidate.rank,
                        int(candidate.selected),
                    ),
                )
                if cursor.lastrowid is None:
                    raise RuntimeError("Failed to insert retrieval candidate")
                ids.append(cursor.lastrowid)
            return ids

    def get_retrieval_candidates(
        self, job_requirement_id: int
    ) -> list[RetrievalCandidate]:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                SELECT id, job_requirement_id, fact_id, method, score, rank, selected, created_at
                FROM retrieval_candidates
                WHERE job_requirement_id = ?
                ORDER BY id
                """,
                (job_requirement_id,),
            )
            rows = cast(
                list[tuple[int, int, int, str, float, int, int, str]],
                cursor.fetchall(),
            )
            return [
                RetrievalCandidate(
                    id=row[0],
                    job_requirement_id=row[1],
                    fact_id=row[2],
                    method=row[3],
                    score=row[4],
                    rank=row[5],
                    selected=bool(row[6]),
                    created_at=row[7],
                )
                for row in rows
            ]
