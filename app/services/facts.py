import time
from collections.abc import Awaitable, Callable

from app.database import SqliteFactStore
from app.schema import FactDraft, ModelFactOutput, ModelFactRun, SourceSpan
from app.services.markdown import get_span_by_sequence, make_source_span


class EvidenceNotInSourceSpan(Exception):
    pass


class SourceSpanNotFound(Exception):
    def __init__(self, document_id: str, sequence: int):
        super().__init__(document_id, sequence)
        self.document_id: str = document_id
        self.sequence: int = sequence


class Facts:
    def __init__(
        self,
        store: SqliteFactStore,
        extractor: Callable[[SourceSpan], Awaitable[ModelFactOutput]],
        model: str,
        prompt_id: str,
        prompt_version: str,
    ) -> None:
        self.store: SqliteFactStore = store
        self.extractor: Callable[[SourceSpan], Awaitable[ModelFactOutput]] = extractor
        self.model: str = model
        self.prompt_id: str = prompt_id
        self.prompt_version: str = prompt_version

    def _locate_span(self, document_id: str, sequence: int) -> SourceSpan:
        document = self.store.get_document(document_id)
        if document is None:
            raise SourceSpanNotFound(document_id, sequence)
        source_spans = make_source_span(document.content)

        selected_span = get_span_by_sequence(source_spans, sequence)

        if selected_span is None:
            raise SourceSpanNotFound(document_id, sequence)

        return selected_span

    def _check_evidence(self, span: SourceSpan, evidence_quote: str) -> None:
        if evidence_quote not in span["body"]:
            raise EvidenceNotInSourceSpan(
                "Evidence quote was not found in the source span"
            )

    def confirm(self, document_id: str, fact_draft: FactDraft) -> None:
        span = self._locate_span(document_id, fact_draft.source_sequence)

        self._check_evidence(span, fact_draft.evidence_quote)
        self.store.save_fact(document_id, fact_draft)

    async def extract(self, document_id: str, sequence: int) -> FactDraft:
        span = self._locate_span(document_id, sequence)
        start_at = time.time()

        try:
            # Extract the fact using the LLM model
            output = await self.extractor(span)

            # Check that the extracted evidence is actually in the source span
            self._check_evidence(span, output.evidence_quote)

        except Exception as e:
            completed_at = time.time()
            _ = self.store.save_model_fact_run(
                model_fact_run=ModelFactRun(
                    document_id=document_id,
                    source_sequence=sequence,
                    model=self.model,
                    prompt_id=self.prompt_id,
                    prompt_version=self.prompt_version,
                    start_at=start_at,
                    completed_at=completed_at,
                    status="failed",
                    output=None,
                    error=f"{type(e).__name__}: {e}",
                )
            )
            raise

        else:
            completed_at = time.time()
            _ = self.store.save_model_fact_run(
                model_fact_run=ModelFactRun(
                    document_id=document_id,
                    source_sequence=sequence,
                    model=self.model,
                    prompt_id=self.prompt_id,
                    prompt_version=self.prompt_version,
                    start_at=start_at,
                    completed_at=completed_at,
                    status="completed",
                    output=output.model_dump_json(),
                    error=None,
                )
            )

        return FactDraft(
            claim=output.claim,
            evidence_quote=output.evidence_quote,
            source_sequence=span["sequence"],
        )
