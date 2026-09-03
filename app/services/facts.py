from collections.abc import Awaitable, Callable
from typing import Protocol

from app.schema import Document, FactDraft, ModelFactOutput, SourceSpan
from app.services.markdown import make_source_span


class EvidenceNotInSourceSpan(Exception):
    pass


class SourceSpanNotFound(Exception):
    def __init__(self, document_id: str, sequence: int):
        super().__init__(document_id, sequence)
        self.document_id: str = document_id
        self.sequence: int = sequence


class FactStore(Protocol):
    def get_document(self, document_id: str) -> Document | None: ...

    def save_fact(
        self, document_id: str, claim: str, evidence_quote: str, source_sequence: int
    ) -> None: ...


class Facts:
    def __init__(
        self,
        store: FactStore,
        draft_model: Callable[[SourceSpan], Awaitable[ModelFactOutput]],
    ) -> None:
        self.store: FactStore = store
        self.draft_model: Callable[[SourceSpan], Awaitable[ModelFactOutput]] = (
            draft_model
        )

    def _locate_span(self, document_id: str, sequence: int) -> SourceSpan:
        document = self.store.get_document(document_id)
        if document is None:
            raise SourceSpanNotFound(document_id, sequence)
        source_spans = make_source_span(document.content)

        selected_span = next(
            (span for span in source_spans if span["sequence"] == sequence),
            None,
        )

        if selected_span is None:
            raise SourceSpanNotFound(document_id, sequence)

        return selected_span

    def _check_evidence(self, span: SourceSpan, evidence_quote: str) -> None:
        if evidence_quote not in span["text"]:
            raise EvidenceNotInSourceSpan()

    def confirm(self, document_id: str, fact_draft: FactDraft) -> None:
        span = self._locate_span(document_id, fact_draft.source_sequence)

        self._check_evidence(span, fact_draft.evidence_quote)
        self.store.save_fact(
            document_id,
            fact_draft.claim,
            fact_draft.evidence_quote,
            fact_draft.source_sequence,
        )

    async def draft(self, document_id: str, sequence: int) -> FactDraft:
        span = self._locate_span(document_id, sequence)
        output = await self.draft_model(span)
        self._check_evidence(span, output.evidence_quote)

        return FactDraft(
            claim=output.claim,
            evidence_quote=output.evidence_quote,
            source_sequence=span["sequence"],
        )
