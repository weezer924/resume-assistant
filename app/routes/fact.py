from fastapi import APIRouter

from app.database import save_fact
from app.schema import ConfirmFactRequest

router = APIRouter()


@router.post("/fact/")
async def post_fact_draft(confirm_fact_request: ConfirmFactRequest):
    save_fact(
        confirm_fact_request.document_id,
        confirm_fact_request.fact_draft.claim,
        confirm_fact_request.fact_draft.evidence_quote,
        confirm_fact_request.fact_draft.source_sequence,
    )
    return {
        "message": "Fact saved",
        "document_id": confirm_fact_request.document_id,
        "fact": confirm_fact_request.fact_draft.model_dump(),
    }
