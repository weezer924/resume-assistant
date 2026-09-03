from uuid import uuid4

from fastapi import APIRouter, HTTPException, UploadFile

from app.database import save_document
from app.services.fact_extraction import extract_fact_draft
from app.services.markdown import make_source_span

router = APIRouter()


@router.post("/documents/import")
async def import_document(file: UploadFile | None = None, sequence: int = 2):
    if not file:
        return {"message": "No upload file sent"}

    contents = await file.read()
    document_id = str(uuid4())
    content = contents.decode("utf-8")

    save_document(document_id, file.filename or "uploaded.md", content)

    source_spans = make_source_span(content)

    selected_span = next(
        (span for span in source_spans if span["sequence"] == sequence),
        None,
    )

    if selected_span is None:
        raise HTTPException(status_code=404, detail="Source span not found")

    # call openAI API modal
    fact_draft = await extract_fact_draft(selected_span)

    if fact_draft.evidence_quote not in selected_span["text"]:
        raise HTTPException(
            status_code=422,
            detail="Model evidence quote is not in the selected source span",
        )

    return {
        "document_id": document_id,
        "fact_draft": fact_draft.model_dump(),
    }
