from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.database import SqliteStore
from app.dependencies import get_facts_service, get_store
from app.schema import Document
from app.services.facts import Facts
from app.services.markdown import make_source_span

router = APIRouter()


@router.post("/documents/import")
async def import_document(
    file: UploadFile,
    store: Annotated[SqliteStore, Depends(get_store)],
):

    document_id = str(uuid4())

    contents = await file.read()

    try:
        content = contents.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=422, detail="Uploaded file must be a UTF-8 encoded text file"
        )

    if content.strip() == "":
        raise HTTPException(status_code=422, detail="Uploaded file is empty")

    spans = make_source_span(content)

    store.save_document_with_spans(
        Document(
            document_id=document_id,
            filename=file.filename or "uploaded.md",
            content=content,
        ),
        spans,
    )

    return {"document_id": document_id, "spans": spans}


@router.post("/documents/{document_id}/spans/{sequence}/facts")
async def post_document_drafts(
    document_id: str,
    sequence: int,
    facts: Annotated[Facts, Depends(get_facts_service)],
):
    fact_drafts = await facts.extract(document_id, sequence)
    return {"fact_drafts": fact_drafts}


@router.get("/documents/{document_id}/review")
def get_document_review(
    document_id: str,
    store: Annotated[SqliteStore, Depends(get_store)],
):
    document = store.get_document(document_id)

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "document_id": document_id,
        "filename": document.filename,
        "spans": store.get_source_spans(document_id),
        "facts": store.get_facts(document_id),
    }
