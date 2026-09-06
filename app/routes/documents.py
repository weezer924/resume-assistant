from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, UploadFile

from app.database import SqliteFactStore
from app.dependencies import get_facts, get_store
from app.schema import Document
from app.services.facts import Facts
from app.services.markdown import make_source_span

router = APIRouter()


@router.post("/documents/import")
async def import_document(
    file: UploadFile,
    store: Annotated[SqliteFactStore, Depends(get_store)],
):

    document_id = str(uuid4())

    contents = await file.read()
    content = contents.decode("utf-8")

    store.save_document(
        Document(
            document_id=document_id,
            filename=file.filename or "uploaded.md",
            content=content,
        )
    )

    spans = make_source_span(content)

    return {"document_id": document_id, "spans": spans}


@router.post("/documents/{document_id}/spans/{sequence}/draft")
async def post_document_drafts(
    document_id: str,
    sequence: int,
    facts: Annotated[Facts, Depends(get_facts)],
):
    fact_draft = await facts.extract(document_id, sequence)
    return {"fact_draft": fact_draft.model_dump()}
