from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, UploadFile

from app.database import save_document_to_db
from app.dependencies import get_facts_by_LLM
from app.services.facts import Facts

router = APIRouter()


@router.post("/documents/import")
async def import_document(
    facts: Annotated[Facts, Depends(get_facts_by_LLM)],
    file: UploadFile | None = None,
    sequence: int = 2,
):
    if not file:
        return {"message": "No upload file sent"}

    document_id = str(uuid4())

    contents = await file.read()
    content = contents.decode("utf-8")

    save_document_to_db(document_id, file.filename or "uploaded.md", content)

    fact_draft = await facts.extract(document_id, sequence)

    return {
        "document_id": document_id,
        "fact_draft": fact_draft.model_dump(),
    }
