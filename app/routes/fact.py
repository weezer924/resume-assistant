from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import get_facts
from app.schema import ConfirmFactRequest, EditFactRequest
from app.services.facts import Facts

router = APIRouter()


@router.post("/fact/")
async def post_fact_draft(
    confirm_fact_request: ConfirmFactRequest,
    facts: Annotated[Facts, Depends(get_facts)],
):

    confirmed = facts.confirm(confirm_fact_request.fact_id)

    return {
        "message": "Fact confirmed",
        "document_id": confirmed.document_id,
        "fact": confirmed.model_dump(),
    }


@router.patch("/facts/{fact_id}")
def edit_fact(
    fact_id: int,
    request: EditFactRequest,
    facts: Annotated[Facts, Depends(get_facts)],
):
    return {"fact": facts.edit(fact_id, request.claim).model_dump()}


@router.post("/facts/{fact_id}/reject")
def reject_fact(
    fact_id: int,
    facts: Annotated[Facts, Depends(get_facts)],
):
    return {"fact": facts.reject(fact_id).model_dump()}
