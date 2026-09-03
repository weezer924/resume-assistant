from typing import TypedDict

from pydantic import BaseModel


class SectionHeader(TypedDict):
    level: int
    title: str


class MarkdownSection(TypedDict):
    level: int
    title: str
    body: list[str]


class SourceSpan(TypedDict):
    section: str
    level: int
    text: str
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
