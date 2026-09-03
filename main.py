import sqlite3
from uuid import uuid4

from fastapi import FastAPI, HTTPException, UploadFile
from openai import AsyncOpenAI
from pydantic import BaseModel

DB_PATH = "database/resume_assistant.db"

app = FastAPI()
client = AsyncOpenAI()


class FactDraft(BaseModel):
    claim: str
    evidence_quote: str
    source_sequence: int


class ConfirmFactRequest(BaseModel):
    document_id: str
    fact_draft: FactDraft


@app.post("/documents/import")
async def import_document(file: UploadFile | None = None, sequence: int = 2):
    if not file:
        return {"message": "No upload file sent"}

    contents = await file.read()
    document_id = str(uuid4())
    content = contents.decode("utf-8")

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            """
            INSERT INTO documents (document_id, filename, content)
            VALUES (?, ?, ?)
            """,
            (document_id, file.filename, content),
        )

    source_spans = await make_source_span(content)

    selected_span = next(
        (span for span in source_spans if span["sequence"] == sequence),
        None,
    )

    if selected_span is None:
        raise HTTPException(status_code=404, detail="Source span not found")

    fact_draft = await extract_fact_draft(selected_span)

    if fact_draft.evidence_quote not in selected_span["text"]:
        raise HTTPException(
            status_code=422,
            detail="Model evidence quote is not in the selected source span",
        )

    return {
        "document_id": document_id,
        # "sourceSpan": source_spans,
        "fact_draft": fact_draft.model_dump(),
    }


@app.post("/fact/")
async def post_fact_draft(confirm_fact_request: ConfirmFactRequest):

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
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
                confirm_fact_request.document_id,
                confirm_fact_request.fact_draft.claim,
                confirm_fact_request.fact_draft.evidence_quote,
                confirm_fact_request.fact_draft.source_sequence,
            ),
        )

    return {
        "message": "Fact saved",
        "document_id": confirm_fact_request.document_id,
        "fact": confirm_fact_request.fact_draft.model_dump(),
    }


@app.get("/")
async def main():
    return {"hello"}


async def make_source_span(content: str):
    source_spans = []
    sequence = 1
    chunks = split_markdown_sections(content)

    for chunk in chunks:
        source_spans.append(
            {
                "section": chunk["title"],
                "level": chunk["level"],
                "text": "\n".join(chunk["body"]),
                "sequence": sequence,
            }
        )
        sequence += 1

    return source_spans


async def extract_fact_draft(source_span) -> FactDraft | None:
    response = await client.responses.parse(
        model="gpt-5-mini",
        input=[
            {
                "role": "developer",
                "content": (
                    "Extract one factual resume claim from the supplied source span. "
                    "Do not add information not present in the source. "
                    "The evidence_quote must be copied exactly from the source."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"source_sequence: {source_span['sequence']}\n"
                    f"section: {source_span['section']}\n"
                    f"text: {source_span['text']}"
                ),
            },
        ],
        text_format=FactDraft,
    )
    # print("status/usage", response.status, response.usage)
    return response.output_parsed


def split_markdown_sections(text: str):
    level_sections = []
    body_lines = []
    current_chunk = None

    for line in text.splitlines():
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            title = line[level:].strip()
            if current_chunk is not None:
                level_sections.append(
                    {
                        "level": current_chunk["level"],
                        "title": current_chunk["title"],
                        "body": body_lines.copy(),
                    }
                )

            current_chunk = {"level": level, "title": title}
            body_lines = []
        else:
            body_lines.append(line)

    if current_chunk is not None:
        level_sections.append(
            {
                "level": current_chunk["level"],
                "title": current_chunk["title"],
                "body": body_lines.copy(),
            }
        )

    return level_sections


def init_db():
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                document_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.execute("""
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


init_db()
