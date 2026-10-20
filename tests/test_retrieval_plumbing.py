from pathlib import Path

import pytest

from app.database import SqliteStore
from app.evaluation.retrieval_cases import (
    assess_case,
    load_cases,
    recall_at_k,
    seed_cases,
)
from app.schema import (
    Document,
    EmbeddingRun,
    Job,
    ModelJobRequirementOutput,
    ModelJobRequirementsOutput,
    RetrievalCandidateDraft,
)
from app.services.jobs import Jobs, RequirementNotInJob

DOCUMENT_ID = "doc1"


@pytest.fixture
def store(tmp_path: Path) -> SqliteStore:
    store = SqliteStore(str(tmp_path / "test.db"))
    store.save_document(
        Document(document_id=DOCUMENT_ID, filename="a.md", content="# A\nhello")
    )
    store.save_job(Job(id="job-1", source_text="Python experience is required."))
    return store


async def stub_requirements(_job: Job) -> ModelJobRequirementsOutput:
    return ModelJobRequirementsOutput(
        requirements=[
            ModelJobRequirementOutput(
                requirement_text="Python experience is required.",
                normalized_requirement="python experience",
                category="technical_skill",
                required_or_preferred="required",
                years_or_level=None,
            )
        ]
    )


async def stub_unmatched(_job: Job) -> ModelJobRequirementsOutput:
    return ModelJobRequirementsOutput(
        requirements=[
            ModelJobRequirementOutput(
                requirement_text="Kubernetes experience is required.",
                normalized_requirement="kubernetes",
                category="technical_skill",
                required_or_preferred="required",
                years_or_level=None,
            )
        ]
    )


async def test_job_extract_records_completed_run(store: SqliteStore):
    jobs = Jobs(store, stub_requirements, "model", "job_extraction", "1.1")
    _ = await jobs.extract("job-1")

    runs = store.get_model_job_runs("job-1")
    assert len(runs) == 1
    assert runs[0].status == "completed"
    assert runs[0].prompt_version == "1.1"
    assert runs[0].output is not None and "Python experience" in runs[0].output
    assert runs[0].error is None
    assert runs[0].completed_at >= runs[0].start_at


async def test_job_extract_records_failed_run_and_saves_nothing(store: SqliteStore):
    jobs = Jobs(store, stub_unmatched, "model", "job_extraction", "1.1")
    with pytest.raises(RequirementNotInJob):
        _ = await jobs.extract("job-1")

    runs = store.get_model_job_runs("job-1")
    assert len(runs) == 1
    assert runs[0].status == "failed"
    assert runs[0].output is None
    assert runs[0].error is not None and "RequirementNotInJob" in runs[0].error
    assert store.get_job_requirements("job-1") == []


def test_fact_embedding_upsert_read_delete(store: SqliteStore):
    fact_id = store.save_fact(DOCUMENT_ID, "claim", "hello", 1, 1)

    store.upsert_fact_embedding(fact_id, "m", [0.1, 0.2])
    store.upsert_fact_embedding(fact_id, "m", [0.3, 0.4])
    assert store.get_fact_embeddings("m") == [(fact_id, [0.3, 0.4])]
    assert store.get_fact_embeddings("other-model") == []

    store.delete_fact_embedding(fact_id)
    assert store.get_fact_embeddings("m") == []


def test_embedding_run_round_trip(store: SqliteStore):
    run_id = store.save_embedding_run(
        EmbeddingRun(
            input_kind="fact",
            input_ref=7,
            model="m",
            start_at=1.0,
            completed_at=2.0,
            status="failed",
            error="RuntimeError: boom",
        )
    )
    assert run_id > 0
    runs = store.get_embedding_runs("fact", 7)
    assert len(runs) == 1
    assert runs[0].status == "failed"
    assert store.get_embedding_runs("requirement", 7) == []


def test_retrieval_candidates_round_trip(store: SqliteStore):
    fact_id = store.save_fact(DOCUMENT_ID, "claim", "hello", 1, 1)
    requirement_id = store.save_job_requirements(
        "job-1",
        [
            ModelJobRequirementOutput(
                requirement_text="Python experience is required.",
                normalized_requirement="python",
                category="technical_skill",
                required_or_preferred="required",
                years_or_level=None,
            )
        ],
    )[0]

    ids = store.save_retrieval_candidates(
        [
            RetrievalCandidateDraft(
                job_requirement_id=requirement_id,
                fact_id=fact_id,
                method="embedding:test",
                score=0.91,
                rank=1,
                selected=True,
            )
        ]
    )
    saved = store.get_retrieval_candidates(requirement_id)
    assert [c.id for c in saved] == ids
    assert saved[0].fact_id == fact_id
    assert saved[0].score == 0.91
    assert saved[0].rank == 1
    assert saved[0].selected is True
    assert saved[0].method == "embedding:test"


def test_fixture_cases_seed_as_confirmed_facts(tmp_path: Path):
    store = SqliteStore(str(tmp_path / "cases.db"))
    cases = load_cases()
    seeded = seed_cases(store, cases)

    confirmed = {fact.id for fact in store.get_confirmed_facts()}
    assert set(seeded.fact_ids.values()) == confirmed
    assert set(seeded.requirement_ids) == {case.id for case in cases.cases}
    for case in cases.cases:
        for key in case.relevant + case.hard_negatives:
            assert key in cases.facts, f"{case.id}: unknown fact key {key}"
        if case.kind == "no_evidence":
            assert case.relevant == []


def test_recall_at_k():
    assert recall_at_k({1, 2}, [2, 9, 1], 3) == 1.0
    assert recall_at_k({1, 2}, [2, 9, 1], 2) == 0.5
    assert recall_at_k({1}, [5, 6], 2) == 0.0
    with pytest.raises(ValueError):
        _ = recall_at_k(set(), [1], 1)


def test_assess_case_reports_hard_negative_above_relevant(tmp_path: Path):
    store = SqliteStore(str(tmp_path / "cases.db"))
    cases = load_cases()
    seeded = seed_cases(store, cases)
    case = next(c for c in cases.cases if c.id == "python_years")

    java = seeded.fact_ids["java_spring_5y"]
    python = seeded.fact_ids["python_django_5y"]
    result = assess_case(case, seeded, [java, python], k=5)

    assert result.recall == 1.0
    assert result.hard_negative_above_relevant == ["java_spring_5y"]
    assert result.ranked_fact_keys == ["java_spring_5y", "python_django_5y"]

    no_evidence = next(c for c in cases.cases if c.id == "kubernetes")
    result = assess_case(no_evidence, seeded, [java], k=5)
    assert result.recall is None
