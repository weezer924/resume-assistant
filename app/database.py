import sqlite3
from typing import cast

from app.schema import Document, FactDraft


class SqliteFactStore:
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
                    evidence_quote TEXT NOT NULL,
                    source_sequence INTEGER NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents(document_id)
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

    def save_fact(
        self,
        document_id: str,
        fact_draft: FactDraft,
    ) -> None:
        with sqlite3.connect(self.db_path) as connection:
            _ = connection.execute(
                """
                        INSERT INTO facts (
                            document_id,
                            claim,
                            evidence_quote,
                            source_sequence
                        )
                        VALUES (?, ?, ?, ?)
                        """,
                (
                    document_id,
                    fact_draft.claim,
                    fact_draft.evidence_quote,
                    fact_draft.source_sequence,
                ),
            )

    def get_facts(self, document_id: str) -> list[FactDraft]:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                SELECT claim, evidence_quote, source_sequence
                FROM facts
                WHERE document_id = ?
                """,
                (document_id,),
            )
            rows = cast(list[tuple[str, str, int]], cursor.fetchall())
            return [
                FactDraft(claim=row[0], evidence_quote=row[1], source_sequence=row[2])
                for row in rows
            ]
