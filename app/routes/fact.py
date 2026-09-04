from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import get_facts
from app.schema import ConfirmFactRequest
from app.services.facts import Facts

router = APIRouter()


@router.post("/fact/")
async def post_fact_draft(
    confirm_fact_request: ConfirmFactRequest,
    facts: Annotated[Facts, Depends(get_facts)],
):

    facts.confirm(confirm_fact_request.document_id, confirm_fact_request.fact_draft)

    return {
        "message": "Fact saved",
        "document_id": confirm_fact_request.document_id,
        "fact": confirm_fact_request.fact_draft.model_dump(),
    }
