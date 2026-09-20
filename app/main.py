from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.routes import documents, fact
from app.services.facts import (
    EvidenceNotInSourceSpan,
    FactNotFound,
    InvalidFactTransition,
    SourceSpanNotFound,
)

app = FastAPI()

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/", include_in_schema=False)
def review_page():
    return FileResponse(FRONTEND_DIR / "index.html")


app.include_router(documents.router)
app.include_router(fact.router)


@app.exception_handler(SourceSpanNotFound)
async def source_span_not_found_handler(_request: Request, _exc: SourceSpanNotFound):
    return JSONResponse(status_code=404, content={"detail": "Source span not found"})


@app.exception_handler(EvidenceNotInSourceSpan)
async def evidence_not_in_source_span(_request: Request, _exc: EvidenceNotInSourceSpan):
    return JSONResponse(
        status_code=422, content={"detail": "Evidence not found in source span"}
    )


@app.exception_handler(FactNotFound)
async def fact_not_found_handler(_request: Request, _exc: FactNotFound):
    return JSONResponse(status_code=404, content={"detail": "Fact not found"})


@app.exception_handler(InvalidFactTransition)
async def invalid_fact_transition_handler(
    _request: Request, exc: InvalidFactTransition
):
    return JSONResponse(status_code=409, content={"detail": str(exc)})
