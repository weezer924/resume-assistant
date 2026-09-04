from typing import TypedDict

from pydantic import BaseModel


class SourceSpan(TypedDict):
    section: str
    level: int
    body: str
    sequence: int


class FactDraft(BaseModel):
    claim: str
    evidence_quote: str
    source_sequence: int


class ConfirmFactRequest(BaseModel):
    document_id: str
    fact_draft: FactDraft


class Document(BaseModel):
    document_id: str
    filename: str
    content: str


class ModelFactOutput(BaseModel):
    claim: str
    evidence_quote: str
