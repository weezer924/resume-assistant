from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.database import init_db
from app.routes import documents, fact
from app.services.facts import EvidenceNotInSourceSpan, SourceSpanNotFound

app = FastAPI()

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


init_db()
