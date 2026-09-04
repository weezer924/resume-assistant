import sqlite3
from typing import cast

from app.schema import Document

DB_PATH = "database/resume_assistant.db"


def init_db():
    with sqlite3.connect(DB_PATH) as connection:
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


def save_document_to_db(document_id: str, filename: str, content: str):
    with sqlite3.connect(DB_PATH) as connection:
        _ = connection.execute(
            """
            INSERT INTO documents (document_id, filename, content)
            VALUES (?, ?, ?)
            """,
            (document_id, filename, content),
        )


class SqliteFactStore:
    def get_document_from_db(self, document_id: str) -> Document | None:
        with sqlite3.connect(DB_PATH) as connection:
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

    def save_fact_to_db(
        self,
        document_id: str,
        claim: str,
        evidence_quote: str,
        source_sequence: int,
    ) -> None:
        with sqlite3.connect(DB_PATH) as connection:
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
                    claim,
                    evidence_quote,
                    source_sequence,
                ),
            )
