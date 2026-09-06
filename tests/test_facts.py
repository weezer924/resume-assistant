from pathlib import Path

import pytest

from app.database import SqliteFactStore
from app.schema import Document, FactDraft, ModelFactOutput, SourceSpan
from app.services.facts import EvidenceNotInSourceSpan, Facts, SourceSpanNotFound

DOCUMENT_ID = "doc1"


@pytest.fixture
def store(tmp_path: Path) -> SqliteFactStore:
    store = SqliteFactStore(str(tmp_path / "test.db"))
    store.save_document(
        Document(
            document_id=DOCUMENT_ID, filename="a.md", content="# A\nhello\n# B\nworld"
        )
    )
    return store


def stub_extractor(claim: str, evidence_quote: str):
    async def extract(_span: SourceSpan) -> ModelFactOutput:
        return ModelFactOutput(claim=claim, evidence_quote=evidence_quote)

    return extract


def test_confirm_saves_fact(store: SqliteFactStore):
    facts = Facts(store, stub_extractor("any", "any"))

    facts.confirm(
        DOCUMENT_ID, FactDraft(claim="c", evidence_quote="world", source_sequence=2)
    )

    assert store.get_facts(DOCUMENT_ID) == [
        FactDraft(claim="c", evidence_quote="world", source_sequence=2)
    ]


def test_confirm_rejects_quote_not_in_span(store: SqliteFactStore):
    facts = Facts(store, stub_extractor("any", "any"))

    with pytest.raises(EvidenceNotInSourceSpan):
        facts.confirm(
            DOCUMENT_ID,
            FactDraft(claim="c", evidence_quote="nothing", source_sequence=2),
        )
    assert store.get_facts(DOCUMENT_ID) == []


def test_confirm_rejects_unknown_document(store: SqliteFactStore):
    facts = Facts(store, stub_extractor("any", "any"))

    with pytest.raises(SourceSpanNotFound):
        facts.confirm(
            "nope", FactDraft(claim="c", evidence_quote="world", source_sequence=2)
        )
    assert store.get_facts(DOCUMENT_ID) == []


def test_confirm_rejects_unknown_sequence(store: SqliteFactStore):
    facts = Facts(store, stub_extractor("any", "any"))

    with pytest.raises(SourceSpanNotFound):
        facts.confirm(
            DOCUMENT_ID,
            FactDraft(claim="c", evidence_quote="world", source_sequence=99),
        )
    assert store.get_facts(DOCUMENT_ID) == []


async def test_extract_returns_candidate(store: SqliteFactStore):
    facts = Facts(store, stub_extractor("c", "world"))

    result = await facts.extract(DOCUMENT_ID, 2)

    assert result == FactDraft(claim="c", evidence_quote="world", source_sequence=2)


async def test_extract_rejects_quote_not_in_span(store: SqliteFactStore):
    facts = Facts(store, stub_extractor("c", "nothing"))

    with pytest.raises(EvidenceNotInSourceSpan):
        _ = await facts.extract(DOCUMENT_ID, 1)


async def test_extract_rejects_unknown_document(store: SqliteFactStore):
    facts = Facts(store, stub_extractor("c", "world"))

    with pytest.raises(SourceSpanNotFound):
        _ = await facts.extract("nope", 1)


async def test_extract_rejects_unknown_sequence(store: SqliteFactStore):
    facts = Facts(store, stub_extractor("c", "world"))

    with pytest.raises(SourceSpanNotFound):
        _ = await facts.extract(DOCUMENT_ID, 99)
