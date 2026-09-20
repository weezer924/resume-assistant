from pathlib import Path
from typing import cast

from fastapi.testclient import TestClient

from app.database import SqliteFactStore
from app.dependencies import get_facts, get_store
from app.main import app
from app.schema import FactDraft, ModelFactOutput, SourceSpan
from app.services.facts import Facts


def test_connected_review_flow(tmp_path: Path):
    store = SqliteFactStore(str(tmp_path / "review.db"))

    async def extractor(span: SourceSpan) -> ModelFactOutput:
        return ModelFactOutput(claim="Built a sample app", evidence_quote=span["body"])

    facts = Facts(store, extractor, "stub", "stub", "1")
    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[get_facts] = lambda: facts
    try:
        with TestClient(app) as client:
            assert client.get("/").status_code == 200
            imported = client.post(
                "/documents/import",
                files={
                    "file": (
                        "sample.md",
                        b"# Project\nBuilt a sample app.",
                        "text/markdown",
                    )
                },
            )
            assert imported.status_code == 200
            doc_id = cast(str, imported.json()["document_id"])
            draft = client.post(f"/documents/{doc_id}/spans/1/draft")
            assert draft.status_code == 200
            candidate = FactDraft.model_validate(draft.json()["fact_draft"])
            confirmed = client.post("/fact/", json={"fact_id": candidate.id})
            assert confirmed.status_code == 200
            assert confirmed.json()["fact"]["status"] == "confirmed"
            edited = client.patch(
                f"/facts/{candidate.id}", json={"claim": "Helped build a sample app"}
            )
            assert edited.status_code == 200
            fact = FactDraft.model_validate(edited.json()["fact"])
            assert fact.id == candidate.id
            assert fact.status == "pending"
            assert fact.confirmed_at is None
            assert fact.original_claim == candidate.claim
            restored = client.get(f"/documents/{doc_id}/review")
            assert restored.status_code == 200
            assert restored.json()["facts"] == [fact.model_dump()]
            assert restored.json()["spans"][0]["body"] == "Built a sample app."
            assert client.get("/documents/missing/review").status_code == 404
    finally:
        app.dependency_overrides.clear()
