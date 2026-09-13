from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from openai import AsyncOpenAI

from app.database import SqliteFactStore
from app.schema import Document, FactDraft, ModelFactOutput, SourceSpan
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


def test_confirm_saves_fact(store: SqliteFactStore):
    facts = Facts(
        store, stub_extractor("any", "any"), "model", "prompt_id", "prompt_version"
    )

    facts.confirm(
        DOCUMENT_ID, FactDraft(claim="c", evidence_quote="world", source_sequence=2)
    )

    assert store.get_facts(DOCUMENT_ID) == [
        FactDraft(claim="c", evidence_quote="world", source_sequence=2)
    ]


def test_confirm_rejects_quote_not_in_span(store: SqliteFactStore):
    facts = Facts(
        store, stub_extractor("any", "any"), "model", "prompt_id", "prompt_version"
    )

    with pytest.raises(EvidenceNotInSourceSpan):
        facts.confirm(
            DOCUMENT_ID,
            FactDraft(claim="c", evidence_quote="nothing", source_sequence=2),
        )
    assert store.get_facts(DOCUMENT_ID) == []


def test_confirm_rejects_unknown_document(store: SqliteFactStore):
    facts = Facts(
        store, stub_extractor("any", "any"), "model", "prompt_id", "prompt_version"
    )

    with pytest.raises(SourceSpanNotFound):
        facts.confirm(
            "nope", FactDraft(claim="c", evidence_quote="world", source_sequence=2)
        )
    assert store.get_facts(DOCUMENT_ID) == []


def test_confirm_rejects_unknown_sequence(store: SqliteFactStore):
    facts = Facts(
        store, stub_extractor("any", "any"), "model", "prompt_id", "prompt_version"
    )

    with pytest.raises(SourceSpanNotFound):
        facts.confirm(
            DOCUMENT_ID,
            FactDraft(claim="c", evidence_quote="world", source_sequence=99),
        )
    assert store.get_facts(DOCUMENT_ID) == []


async def test_extract_returns_candidate(store: SqliteFactStore):
    facts = Facts(
        store, stub_extractor("c", "world"), "model", "prompt_id", "prompt_version"
    )

    result = await facts.extract(DOCUMENT_ID, 2)

    assert result == FactDraft(claim="c", evidence_quote="world", source_sequence=2)


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

    assert result == FactDraft(claim="c", evidence_quote="world", source_sequence=2)

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

    assert fact_draft == FactDraft(
        claim="c",
        evidence_quote="saved text",
        source_sequence=1,
    )


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
