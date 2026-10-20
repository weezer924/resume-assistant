"""Fixed retrieval cases (spec 10.5): loading, seeding, and Recall@K.

Pure helpers. Retrieval itself lives in app/services and is passed in as ranked
fact ids, so this module never calls a model.
"""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from app.database import SqliteStore
from app.schema import Document, Job, ModelJobRequirementOutput, SourceSpan
from app.services.markdown import make_source_span

FIXTURE_DIR = Path(__file__).resolve().parent.parent.parent / "tests" / "fixtures"
CASES_PATH = FIXTURE_DIR / "retrieval_cases.json"


class SeedFact(BaseModel):
    claim: str
    evidence_quote: str
    source_sequence: int


class RetrievalCase(BaseModel):
    id: str
    kind: Literal["answerable", "no_evidence"]
    requirement: ModelJobRequirementOutput
    relevant: list[str]
    hard_negatives: list[str]
    note: str


class RetrievalCases(BaseModel):
    description: str
    document: str
    facts: dict[str, SeedFact]
    cases: list[RetrievalCase]


class SeededCases(BaseModel):
    """Fixture keys resolved to the ids the store assigned."""

    document_id: str
    job_id: str
    fact_ids: dict[str, int]
    requirement_ids: dict[str, int]


def load_cases(path: Path = CASES_PATH) -> RetrievalCases:
    return RetrievalCases.model_validate_json(path.read_text(encoding="utf-8"))


def seed_cases(store: SqliteStore, cases: RetrievalCases) -> SeededCases:
    """Insert the resume, every fixture fact as *confirmed*, and one Job holding
    every case requirement. Bypasses LLM extraction on purpose: the corpus must
    be identical on every run for Recall@K to be comparable."""
    resume_path = FIXTURE_DIR / cases.document
    content = resume_path.read_text(encoding="utf-8")
    document_id = f"fixture:{cases.document}"
    spans: list[SourceSpan] = make_source_span(content)
    store.save_document_with_spans(
        Document(document_id=document_id, filename=cases.document, content=content),
        spans,
    )

    fact_ids: dict[str, int] = {}
    for key, fact in cases.facts.items():
        span = store.get_source_span(document_id, fact.source_sequence)
        if span is None or fact.evidence_quote not in span["body"]:
            raise ValueError(
                f"fixture fact {key!r}: quote not in span {fact.source_sequence}"
            )
        fact_id = store.save_fact(
            document_id, fact.claim, fact.evidence_quote, fact.source_sequence, 0
        )
        if store.confirm_fact(fact_id) is None:
            raise RuntimeError(f"fixture fact {key!r} could not be confirmed")
        fact_ids[key] = fact_id

    job_id = "fixture:retrieval_cases"
    store.save_job(
        Job(
            id=job_id,
            source_text="\n".join(c.requirement.requirement_text for c in cases.cases),
        )
    )
    requirement_ids = dict(
        zip(
            [c.id for c in cases.cases],
            store.save_job_requirements(job_id, [c.requirement for c in cases.cases]),
            strict=True,
        )
    )
    return SeededCases(
        document_id=document_id,
        job_id=job_id,
        fact_ids=fact_ids,
        requirement_ids=requirement_ids,
    )


def recall_at_k(relevant: set[int], ranked: list[int], k: int) -> float:
    """Share of relevant ids that appear in the top k. Undefined (ValueError)
    when nothing is relevant: no-evidence cases are inspected, not scored."""
    if not relevant:
        raise ValueError("recall_at_k is undefined for a case with no relevant ids")
    return len(relevant & set(ranked[:k])) / len(relevant)


class CaseResult(BaseModel):
    case_id: str
    kind: Literal["answerable", "no_evidence"]
    k: int
    ranked_fact_keys: list[str]
    recall: float | None
    hard_negative_above_relevant: list[str]


def assess_case(
    case: RetrievalCase, seeded: SeededCases, ranked_fact_ids: list[int], k: int
) -> CaseResult:
    """Turn one retrieval result into an inspectable row: Recall@K for answerable
    cases, and which labelled hard negatives outranked the worst relevant fact."""
    id_to_key = {fact_id: key for key, fact_id in seeded.fact_ids.items()}
    ranked_keys = [
        id_to_key.get(fact_id, f"unknown:{fact_id}") for fact_id in ranked_fact_ids
    ]

    recall: float | None = None
    if case.kind == "answerable":
        recall = recall_at_k(
            {seeded.fact_ids[key] for key in case.relevant}, ranked_fact_ids, k
        )

    positions = {key: index for index, key in enumerate(ranked_keys)}
    worst_relevant = max(
        (positions.get(key, len(ranked_keys)) for key in case.relevant), default=-1
    )
    hard_above = [
        key
        for key in case.hard_negatives
        if key in positions and positions[key] < worst_relevant
    ]
    return CaseResult(
        case_id=case.id,
        kind=case.kind,
        k=k,
        ranked_fact_keys=ranked_keys[:k],
        recall=recall,
        hard_negative_above_relevant=hard_above,
    )
