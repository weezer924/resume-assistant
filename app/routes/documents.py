from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.database import save_document
from app.dependencies import get_facts
from app.services.facts import EvidenceNotInSourceSpan, Facts, SourceSpanNotFound

router = APIRouter()


@router.post("/documents/import")
async def import_document(
    facts: Annotated[Facts, Depends(get_facts)],
    file: UploadFile | None = None,
    sequence: int = 2,
):
    if not file:
        return {"message": "No upload file sent"}

    contents = await file.read()
    document_id = str(uuid4())
    content = contents.decode("utf-8")

    save_document(document_id, file.filename or "uploaded.md", content)

    try:
        fact_draft = await facts.draft(document_id, sequence)
    except SourceSpanNotFound:
        raise HTTPException(status_code=404, detail="Source span not found")
    except EvidenceNotInSourceSpan:
        raise HTTPException(
            status_code=422, detail="Evidence quote is not in the selected source span"
        )

    return {
        "document_id": document_id,
        "fact_draft": fact_draft.model_dump(),
    }
