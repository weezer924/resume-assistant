from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from openai import AsyncOpenAI

from app.database import SqliteFactStore
from app.schema import Document, ModelFactOutput, SourceSpan
from app.services.fact_extraction import OpenAIExtractor
from app.services.facts import (
    EvidenceNotInSourceSpan,
    Facts,
    SourceSpanNotFound,
)

DOCUMENT_ID = "doc1"


@pytest.fixture
def store(tmp_path: Path) -> SqliteFactStore:
    store = SqliteFactStore(str(tmp_path / "test.db"))
    store.save_document(
        Document(
            document_id=DOCUMENT_ID, filename="a.md", content="# A\nhello\n# B\nworld"
        )
    )

    source_span_1 = SourceSpan(
        section="A",
        level=1,
        body="hello",
        sequence=1,
    )

    source_span_2 = SourceSpan(
        section="B",
        level=1,
        body="world",
        sequence=2,
    )

    store.save_source_span(DOCUMENT_ID, source_span_1)
    store.save_source_span(DOCUMENT_ID, source_span_2)
    return store


def stub_extractor(claim: str, evidence_quote: str):
    async def extract(_span: SourceSpan) -> ModelFactOutput:
        return ModelFactOutput(claim=claim, evidence_quote=evidence_quote)

    return extract


async def failing_extractor(_span: SourceSpan) -> ModelFactOutput:
    raise RuntimeError("Synthetic model failure")


async def fake_parse(**_kwargs: object):
    return SimpleNamespace(output_parsed=None)


async def test_confirm_updates_pending_candidate(store: SqliteFactStore):
    facts = Facts(
        store, stub_extractor("c", "world"), "model", "prompt_id", "prompt_version"
    )

    candidate = await facts.extract(DOCUMENT_ID, 2)
    confirmed = facts.confirm(candidate.id)

    result = store.get_fact(candidate.id)

    assert result is not None
    assert result == confirmed
    assert result.id == candidate.id
    assert len(store.get_facts(DOCUMENT_ID)) == 1
    assert result.status == "confirmed"
    assert result.confirmed_at is not None


async def test_extract_returns_candidate(store: SqliteFactStore):
    facts = Facts(
        store, stub_extractor("c", "world"), "model", "prompt_id", "prompt_version"
    )

    result = await facts.extract(DOCUMENT_ID, 2)

    assert result.claim == "c"
    assert result.evidence_quote == "world"
    assert result.source_sequence == 2


async def test_extract_rejects_quote_not_in_span(store: SqliteFactStore):
    facts = Facts(
        store, stub_extractor("c", "nothing"), "model", "prompt_id", "prompt_version"
    )

    with pytest.raises(EvidenceNotInSourceSpan):
        _ = await facts.extract(DOCUMENT_ID, 1)


async def test_extract_rejects_unknown_document(store: SqliteFactStore):
    facts = Facts(
        store, stub_extractor("c", "world"), "model", "prompt_id", "prompt_version"
    )

    with pytest.raises(SourceSpanNotFound):
        _ = await facts.extract("nope", 1)


async def test_extract_rejects_unknown_sequence(store: SqliteFactStore):
    facts = Facts(
        store, stub_extractor("c", "world"), "model", "prompt_id", "prompt_version"
    )

    with pytest.raises(SourceSpanNotFound):
        _ = await facts.extract(DOCUMENT_ID, 99)


async def test_extract_modal_fact_run_error_not_in_source_span(store: SqliteFactStore):
    facts = Facts(
        store, stub_extractor("c", "nothing"), "model", "prompt_id", "prompt_version"
    )

    with pytest.raises(EvidenceNotInSourceSpan):
        _ = await facts.extract(DOCUMENT_ID, 2)

    # Check that a failed model fact run was saved
    runs = store.get_model_fact_runs(DOCUMENT_ID)
    assert len(runs) == 1
    run = runs[0]
    assert run.status == "failed"
    assert run.error is not None
    assert run.error.startswith("EvidenceNotInSourceSpan")


async def test_extract_modal_fact_run_error_runtime_error(
    store: SqliteFactStore,
):
    facts = Facts(store, failing_extractor, "model", "prompt_id", "prompt_version")

    with pytest.raises(RuntimeError):
        _ = await facts.extract(DOCUMENT_ID, 2)

    # Check that a failed model fact run was saved
    runs = store.get_model_fact_runs(DOCUMENT_ID)
    assert len(runs) == 1
    run = runs[0]
    assert run.status == "failed"
    assert run.error is not None
    assert run.error.startswith("RuntimeError")


async def test_extract_modal_fact_completed(store: SqliteFactStore):
    facts = Facts(
        store, stub_extractor("c", "world"), "model", "prompt_id", "prompt_version"
    )

    result = await facts.extract(DOCUMENT_ID, 2)

    assert result.claim == "c"
    assert result.evidence_quote == "world"
    assert result.source_sequence == 2

    # Check that a successful model fact run was saved
    runs = store.get_model_fact_runs(DOCUMENT_ID)
    assert len(runs) == 1
    run = runs[0]
    assert run.status == "completed"
    assert run.error is None
    assert run.output is not None
    saved_output = ModelFactOutput.model_validate_json(run.output)
    assert saved_output == ModelFactOutput(claim="c", evidence_quote="world")


async def test_is_using_extract_modal_fact(store: SqliteFactStore):
    document = Document(document_id="doc", filename="doc.md", content="# A\nold text")
    saved_source_span = SourceSpan(
        section="",
        level=1,
        body="saved text",
        sequence=1,
    )

    store.save_document_with_spans(document, [saved_source_span])

    facts = Facts(
        store, stub_extractor("c", "saved text"), "model", "prompt_id", "prompt_version"
    )

    fact_draft = await facts.extract(document.document_id, 1)

    assert fact_draft.claim == "c"
    assert fact_draft.evidence_quote == "saved text"
    assert fact_draft.source_sequence == 1


async def test_extract_output_parsed_none():
    client = MagicMock(spec=AsyncOpenAI)
    client.responses = SimpleNamespace(
        parse=AsyncMock(return_value=SimpleNamespace(output_parsed=None))
    )

    extractor = OpenAIExtractor(client, "test-model")
    span: SourceSpan = {
        "section": "Experience",
        "level": 1,
        "body": "Built a sample application.",
        "sequence": 1,
    }

    with pytest.raises(
        RuntimeError,
        match="Model did not return a fact draft",
    ):
        _ = await extractor(span)


async def test_extract_saves_pending_candidate(store: SqliteFactStore):
    facts = Facts(
        store, stub_extractor("c", "world"), "model", "prompt_id", "prompt_version"
    )

    result = await facts.extract(DOCUMENT_ID, 2)
    saved = store.get_fact(result.id)

    assert saved is not None
    assert saved == result
    assert saved.status == "pending"
    assert saved.claim == "c"
    assert saved.original_claim == "c"
    assert saved.evidence_quote == "world"
    assert saved.document_id == DOCUMENT_ID
    assert saved.source_sequence == 2
    assert saved.created_at is not None
    assert saved.updated_at is not None
    assert saved.confirmed_at is None
    assert saved.extraction_run_id is not None

    run = store.get_model_fact_run(saved.extraction_run_id)
    assert run is not None
    assert run.status == "completed"
    assert run.document_id == DOCUMENT_ID
    assert run.source_sequence == 2


async def test_edit_returns_confirmed_fact_to_pending(store: SqliteFactStore):
    facts = Facts(
        store,
        stub_extractor("original_claim", "hello"),
        "model",
        "prompt_id",
        "prompt_version",
    )

    candidate = await facts.extract(DOCUMENT_ID, 1)

    _ = facts.confirm(candidate.id)
    _ = facts.edit(candidate.id, "edited claim")
    edited_candidate = store.get_fact(candidate.id)

    assert edited_candidate is not None
    assert edited_candidate.id == candidate.id
    assert edited_candidate.status == "pending"
    assert edited_candidate.confirmed_at is None
    assert edited_candidate.original_claim == candidate.original_claim
    assert edited_candidate.claim == "edited claim"
    assert edited_candidate.evidence_quote == candidate.evidence_quote
    assert edited_candidate.extraction_run_id == candidate.extraction_run_id
    assert edited_candidate.document_id == candidate.document_id
    assert edited_candidate.source_sequence == candidate.source_sequence

    assert len(store.get_facts(DOCUMENT_ID)) == 1


async def test_reject_preserves_fact(store: SqliteFactStore):
    facts = Facts(
        store,
        stub_extractor("original_claim", "hello"),
        "model",
        "prompt_id",
        "prompt_version",
    )

    candidate = await facts.extract(DOCUMENT_ID, 1)

    _ = facts.confirm(candidate.id)
    result = facts.reject(candidate.id)
    rejected_candidate = store.get_fact(candidate.id)

    assert rejected_candidate is not None
    assert result == rejected_candidate
    assert rejected_candidate.id == candidate.id
    assert rejected_candidate.status == "rejected"
    assert rejected_candidate.confirmed_at is None
    assert rejected_candidate.original_claim == candidate.original_claim
    assert rejected_candidate.claim == candidate.claim
    assert rejected_candidate.evidence_quote == candidate.evidence_quote
    assert rejected_candidate.extraction_run_id == candidate.extraction_run_id
    assert rejected_candidate.document_id == candidate.document_id
    assert rejected_candidate.source_sequence == candidate.source_sequence

    assert len(store.get_facts(DOCUMENT_ID)) == 1
