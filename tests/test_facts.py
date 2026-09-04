import pytest

from app.schema import Document, FactDraft, ModelFactOutput, SourceSpan
from app.services.facts import EvidenceNotInSourceSpan, Facts, SourceSpanNotFound


class FakeStore:
    def __init__(self) -> None:
        self.documents: dict[str, Document] = {}
        self.saved: list[tuple[str, str, str, int]] = []

    def get_document_from_db(self, document_id: str) -> Document | None:
        return self.documents.get(document_id)

    def save_fact_to_db(
        self, document_id: str, claim: str, evidence_quote: str, source_sequence: int
    ) -> None:
        self.saved.append((document_id, claim, evidence_quote, source_sequence))


def stub_extractor(claim: str, evidence_quote: str):
    async def extract(_span: SourceSpan) -> ModelFactOutput:
        return ModelFactOutput(claim=claim, evidence_quote=evidence_quote)

    return extract


def test_confirm_saves_fact():
    store = FakeStore()
    store.documents["doc1"] = Document(
        document_id="doc1", filename="a.md", content="# A\nhello\n# B\nworld"
    )
    facts = Facts(store, stub_extractor("any", "any"))

    facts.confirm(
        "doc1", FactDraft(claim="c", evidence_quote="world", source_sequence=2)
    )

    assert store.saved == [("doc1", "c", "world", 2)]


def test_confirm_rejects_quote_not_in_span():
    store = FakeStore()
    store.documents["doc1"] = Document(
        document_id="doc1", filename="a.md", content="# A\nhello\n# B\nworld"
    )

    facts = Facts(store, stub_extractor("any", "any"))
    with pytest.raises(EvidenceNotInSourceSpan):
        facts.confirm(
            "doc1", FactDraft(claim="c", evidence_quote="nothing", source_sequence=2)
        )
    assert store.saved == []


def test_confirm_rejects_unknown_document():
    store = FakeStore()
    store.documents["doc1"] = Document(
        document_id="doc1", filename="a.md", content="# A\nhello\n# B\nworld"
    )

    facts = Facts(store, stub_extractor("any", "any"))
    with pytest.raises(SourceSpanNotFound):
        facts.confirm(
            "nope", FactDraft(claim="c", evidence_quote="nothing", source_sequence=2)
        )
    assert store.saved == []


def test_confirm_rejects_unknown_sequence():
    store = FakeStore()
    store.documents["doc1"] = Document(
        document_id="doc1", filename="a.md", content="# A\nhello\n# B\nworld"
    )

    facts = Facts(store, stub_extractor("any", "any"))
    with pytest.raises(SourceSpanNotFound):
        facts.confirm(
            "doc1", FactDraft(claim="c", evidence_quote="nothing", source_sequence=99)
        )
    assert store.saved == []


async def test_extract_returns_candidate():
    store = FakeStore()
    store.documents["doc1"] = Document(
        document_id="doc1", filename="a.md", content="# A\nhello\n# B\nworld"
    )

    facts = Facts(store, stub_extractor("c", "world"))

    result = await facts.extract("doc1", 2)
    assert result == FactDraft(claim="c", evidence_quote="world", source_sequence=2)


async def test_extract_rejects_quote_not_in_span():
    store = FakeStore()
    store.documents["doc1"] = Document(
        document_id="doc1", filename="a.md", content="# A\nhello\n# B\nworld"
    )

    facts = Facts(store, stub_extractor("c", "nothing"))
    with pytest.raises(EvidenceNotInSourceSpan):
        _ = await facts.extract("doc1", 1)


async def test_extract_rejects_unknown_document():
    store = FakeStore()
    store.documents["doc1"] = Document(
        document_id="doc1", filename="a.md", content="# A\nhello\n# B\nworld"
    )

    facts = Facts(store, stub_extractor("c", "nothing"))
    with pytest.raises(SourceSpanNotFound):
        _ = await facts.extract("nope", 1)


async def test_extract_rejects_unknown_sequence():
    store = FakeStore()
    store.documents["doc1"] = Document(
        document_id="doc1", filename="a.md", content="# A\nhello\n# B\nworld"
    )

    facts = Facts(store, stub_extractor("c", "nothing"))
    with pytest.raises(SourceSpanNotFound):
        _ = await facts.extract("doc1", 99)
