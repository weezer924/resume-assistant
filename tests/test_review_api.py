from pathlib import Path
from typing import cast

from fastapi.testclient import TestClient

from app.database import SqliteStore
from app.dependencies import get_facts_service, get_job_requirements_service, get_store
from app.main import app
from app.schema import (
    FactDraft,
    Job,
    ModelFactOutput,
    ModelFactsOutput,
    ModelJobRequirementOutput,
    ModelJobRequirementsOutput,
    SourceSpan,
)
from app.services.facts import Facts
from app.services.jobs import Jobs


def test_connected_review_flow(tmp_path: Path):
    store = SqliteStore(str(tmp_path / "review.db"))

    async def extractor(span: SourceSpan) -> ModelFactsOutput:
        return ModelFactsOutput(
            facts=[ModelFactOutput(claim="test claim", evidence_quote=span["body"])]
        )

    facts = Facts(store, extractor, "model", "prompt_id", "1")

    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[get_facts_service] = lambda: facts

    try:
        with TestClient(app) as client:
            assert client.get("/").status_code == 200
            imported = client.post(
                "/documents/import",
                files={
                    "file": (
                        "sample.md",
                        b"# Project\ntest claim",
                        "text/markdown",
                    )
                },
            )
            assert imported.status_code == 200
            doc_id = cast(str, imported.json()["document_id"])

            response = client.post(f"/documents/{doc_id}/spans/1/facts")
            assert response.status_code == 200

            raw_facts = cast(list[object], response.json()["fact_drafts"])
            fact_drafts = [FactDraft.model_validate(item) for item in raw_facts]
            assert len(fact_drafts) == 1
            candidate = fact_drafts[0]

            confirmed = client.post("/fact/", json={"fact_id": candidate.id})
            assert confirmed.status_code == 200
            assert confirmed.json()["fact"]["status"] == "confirmed"

            edited = client.patch(
                f"/facts/{candidate.id}", json={"claim": "edited test claim"}
            )
            assert edited.status_code == 200
            fact = FactDraft.model_validate(edited.json()["fact"])

            assert fact.id == candidate.id
            assert fact.claim == "edited test claim"
            assert fact.status == "pending"
            assert fact.confirmed_at is None
            assert fact.original_claim == candidate.claim

            review_response = client.get(f"/documents/{doc_id}/review")

            assert review_response.status_code == 200
            assert review_response.json()["facts"] == [fact.model_dump()]
            assert review_response.json()["spans"][0]["body"] == "test claim"
            assert client.get("/documents/missing/review").status_code == 404

    finally:
        app.dependency_overrides.clear()


def test_fact_reject_api(tmp_path: Path):
    store = SqliteStore(str(tmp_path / "review.db"))

    async def extractor(span: SourceSpan) -> ModelFactsOutput:
        return ModelFactsOutput(
            facts=[ModelFactOutput(claim="test claim", evidence_quote=span["body"])]
        )

    facts = Facts(store, extractor, "model", "prompt_id", "1")

    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[get_facts_service] = lambda: facts

    try:
        with TestClient(app) as client:
            assert client.get("/").status_code == 200
            imported = client.post(
                "/documents/import",
                files={
                    "file": (
                        "sample.md",
                        b"# Project\ntest claim",
                        "text/markdown",
                    )
                },
            )

            assert imported.status_code == 200
            doc_id = cast(str, imported.json()["document_id"])

            response = client.post(f"/documents/{doc_id}/spans/1/facts")
            assert response.status_code == 200

            raw_facts = cast(list[object], response.json()["fact_drafts"])
            fact_drafts = [FactDraft.model_validate(item) for item in raw_facts]
            assert len(fact_drafts) == 1

            candidate = fact_drafts[0]

            rejected = client.post(
                f"/facts/{candidate.id}/reject",
            )
            assert rejected.status_code == 200, rejected.text

            fact = FactDraft.model_validate(rejected.json()["fact"])
            assert fact.status == "rejected"
            assert fact.id == candidate.id
            assert store.get_fact(candidate.id) == fact

    finally:
        app.dependency_overrides.clear()


def test_job_write_api(tmp_path: Path):
    store = SqliteStore(str(tmp_path / "review.db"))

    app.dependency_overrides[get_store] = lambda: store

    source_text = "we need a python engineer."
    try:
        with TestClient(app) as client:
            response = client.post("/jobs", json={"source_text": source_text})

            assert response.status_code == 200

            job = Job.model_validate(response.json()["job"])

            assert store.get_job(job.id) == job
            assert job.id != ""
            assert job.source_text == source_text

            fetched = client.get(f"/jobs/{job.id}")
            assert fetched.status_code == 200, fetched.text
            assert Job.model_validate(fetched.json()["job"]) == job

    finally:
        app.dependency_overrides.clear()


def test_get_missing_job_returns_404(tmp_path: Path):
    store = SqliteStore(str(tmp_path / "review.db"))
    app.dependency_overrides[get_store] = lambda: store

    try:
        with TestClient(app) as client:
            response = client.get("/jobs/missing-job")
            assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_get_requirement_id_from_job_id(tmp_path: Path):
    store = SqliteStore(str(tmp_path / "review.db"))

    async def job_extractor(_job: Job) -> ModelJobRequirementsOutput:
        return ModelJobRequirementsOutput(
            requirements=[
                ModelJobRequirementOutput(
                    requirement_text="Fast API framework experience",
                    normalized_requirement="Fast API experience",
                    category="Tech",
                    required_or_preferred="required",
                    years_or_level=None,
                ),
                ModelJobRequirementOutput(
                    requirement_text="Have a knowledge of MLOps",
                    normalized_requirement="MLOps experience",
                    category="Tech",
                    required_or_preferred="preferred",
                    years_or_level=None,
                ),
            ]
        )

    jobs = Jobs(store, job_extractor, "model", "prompt_id", "1")

    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[get_job_requirements_service] = lambda: jobs

    try:
        with TestClient(app) as client:
            imported = client.post(
                "/jobs",
                json={
                    "source_text": "Fast API framework experience, Have a knowledge of MLOps"
                },
            )

            assert imported.status_code == 200
            job = Job.model_validate(imported.json()["job"])
            extracted = client.post(f"/jobs/{job.id}/requirements/extract")

            assert extracted.status_code == 200, extracted.text

            requirements = store.get_job_requirements(job.id)

            assert len(requirements) == 2
            assert requirements[0].id != requirements[1].id
            assert requirements[0].requirement_text == "Fast API framework experience"
            assert requirements[0].required_or_preferred == "required"
            assert requirements[1].requirement_text == "Have a knowledge of MLOps"
            assert requirements[1].required_or_preferred == "preferred"

    finally:
        app.dependency_overrides.clear()
