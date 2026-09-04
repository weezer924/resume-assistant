from collections.abc import Awaitable, Callable
from typing import Protocol

from app.schema import Document, FactDraft, ModelFactOutput, SourceSpan
from app.services.markdown import get_span_by_sequence, make_source_span


class EvidenceNotInSourceSpan(Exception):
    pass


class SourceSpanNotFound(Exception):
    def __init__(self, document_id: str, sequence: int):
        super().__init__(document_id, sequence)
        self.document_id: str = document_id
        self.sequence: int = sequence


class FactStore(Protocol):
    def get_document_from_db(self, document_id: str) -> Document | None: ...

    def save_fact_to_db(
        self, document_id: str, claim: str, evidence_quote: str, source_sequence: int
    ) -> None: ...


class Facts:
    def __init__(
        self,
        store: FactStore,
        extractor: Callable[[SourceSpan], Awaitable[ModelFactOutput]],
    ) -> None:
        self.store: FactStore = store
        self.extractor: Callable[[SourceSpan], Awaitable[ModelFactOutput]] = extractor

    def _locate_span(self, document_id: str, sequence: int) -> SourceSpan:
        document = self.store.get_document_from_db(document_id)
        if document is None:
            raise SourceSpanNotFound(document_id, sequence)
        source_spans = make_source_span(document.content)

        selected_span = get_span_by_sequence(source_spans, sequence)

        if selected_span is None:
            raise SourceSpanNotFound(document_id, sequence)

        return selected_span

    def _check_evidence(self, span: SourceSpan, evidence_quote: str) -> None:
        if evidence_quote not in span["body"]:
            raise EvidenceNotInSourceSpan()

    def confirm(self, document_id: str, fact_draft: FactDraft) -> None:
        span = self._locate_span(document_id, fact_draft.source_sequence)

        self._check_evidence(span, fact_draft.evidence_quote)
        self.store.save_fact_to_db(
            document_id,
            fact_draft.claim,
            fact_draft.evidence_quote,
            fact_draft.source_sequence,
        )

    # 从 span 抽一条候选
    async def extract(self, document_id: str, sequence: int) -> FactDraft:
        span = self._locate_span(document_id, sequence)
        output = await self.extractor(span)
        self._check_evidence(span, output.evidence_quote)

        return FactDraft(
            claim=output.claim,
            evidence_quote=output.evidence_quote,
            source_sequence=span["sequence"],
        )
