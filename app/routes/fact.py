from typing import Annotated

from fastapi import APIRouter, Depends
from starlette.exceptions import HTTPException

from app.dependencies import get_facts
from app.schema import ConfirmFactRequest
from app.services.facts import EvidenceNotInSourceSpan, Facts, SourceSpanNotFound

router = APIRouter()


@router.post("/fact/")
async def post_fact_draft(
    confirm_fact_request: ConfirmFactRequest,
    facts: Annotated[Facts, Depends(get_facts)],
):
    try:
        facts.confirm(confirm_fact_request.document_id, confirm_fact_request.fact_draft)
    except SourceSpanNotFound:
        raise HTTPException(status_code=404, detail="Source span not found")
    except EvidenceNotInSourceSpan:
        raise HTTPException(
            status_code=422,
            detail="Evidence quote is not in the selected source span",
        )

    return {
        "message": "Fact saved",
        "document_id": confirm_fact_request.document_id,
        "fact": confirm_fact_request.fact_draft.model_dump(),
    }
