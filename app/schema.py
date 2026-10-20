from typing import Literal, TypedDict

from pydantic import BaseModel


# API request body
class ConfirmFactRequest(BaseModel):
    fact_id: int


class EditFactRequest(BaseModel):
    claim: str


class CreateJobRequest(BaseModel):
    source_text: str


# LLM output
class ModelFactOutput(BaseModel):
    claim: str
    evidence_quote: str


class ModelFactsOutput(BaseModel):
    facts: list[ModelFactOutput]


class ModelJobRequirementOutput(BaseModel):
    requirement_text: str
    normalized_requirement: str
    category: str
    required_or_preferred: Literal["required", "preferred"]
    years_or_level: str | None


class ModelJobRequirementsOutput(BaseModel):
    requirements: list[ModelJobRequirementOutput]


# DB
class Document(BaseModel):
    document_id: str
    filename: str
    content: str


class SourceSpan(TypedDict):
    section: str
    level: int
    body: str
    sequence: int


class FactDraft(BaseModel):
    id: int
    document_id: str
    claim: str
    evidence_quote: str
    original_claim: str
    source_sequence: int
    status: Literal["pending", "confirmed", "rejected"]
    extraction_run_id: int | None
    confirmed_at: str | None
    created_at: str
    updated_at: str


class Job(BaseModel):
    id: str
    source_text: str


class JobRequirement(ModelJobRequirementOutput):
    id: int
    job_id: str


class ModelFactRun(BaseModel):
    document_id: str
    source_sequence: int
    model: str
    prompt_id: str
    prompt_version: str
    start_at: float
    completed_at: float
    status: str
    output: str | None
    error: str | None


class ExtractionConfig(BaseModel):
    model: str
    prompt_id: str
    prompt_version: str


class ModelJobRun(BaseModel):
    job_id: str
    model: str
    prompt_id: str
    prompt_version: str
    start_at: float
    completed_at: float
    status: str
    output: str | None
    error: str | None


class EmbeddingRun(BaseModel):
    """One embedding API call. input_kind/input_ref identify what was embedded:
    ("fact", fact id) for index rows, ("requirement", requirement id) for queries."""

    input_kind: Literal["fact", "requirement"]
    input_ref: int
    model: str
    start_at: float
    completed_at: float
    status: str
    error: str | None


class RetrievalCandidateDraft(BaseModel):
    job_requirement_id: int
    fact_id: int
    method: str
    score: float
    rank: int
    selected: bool


class RetrievalCandidate(RetrievalCandidateDraft):
    id: int
    created_at: str
