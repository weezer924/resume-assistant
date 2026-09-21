from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends

from app.database import SqliteStore
from app.dependencies import get_store
from app.schema import CreateJobRequest, Job

router = APIRouter()


@router.post("/jobs")
def post_job(
    request: CreateJobRequest, store: Annotated[SqliteStore, Depends(get_store)]
):

    job_id = str(uuid4())

    job = Job(id=job_id, source_text=request.source_text)

    store.save_job(job)
    return {"job": store.get_job(job_id)}
