from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from app.database import SqliteStore
from app.dependencies import get_job_requirements_service, get_store
from app.schema import CreateJobRequest, Job
from app.services.jobs import Jobs

router = APIRouter()


@router.post("/jobs")
def post_job(
    request: CreateJobRequest, store: Annotated[SqliteStore, Depends(get_store)]
):

    job_id = str(uuid4())

    job = Job(id=job_id, source_text=request.source_text)

    store.save_job(job)
    return {"job": store.get_job(job_id)}


@router.get("/jobs/{job_id}")
def get_job(job_id: str, store: Annotated[SqliteStore, Depends(get_store)]):
    job = store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job": job}


@router.post("/jobs/{job_id}/requirements/extract")
async def post_job_extract(
    job_id: str, jobs: Annotated[Jobs, Depends(get_job_requirements_service)]
):
    requirements = await jobs.extract(job_id)

    return {"requirements": requirements}
