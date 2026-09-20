import time
from collections.abc import Awaitable, Callable

from app.database import SqliteFactStore
from app.schema import FactDraft, ModelFactOutput, ModelFactRun, SourceSpan


class FactNotFound(Exception):
    pass


class InvalidFactTransition(Exception):
    pass


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

    # 对应的文档和原文片段存在
    def _locate_span(self, document_id: str, sequence: int) -> SourceSpan:
        document = self.store.get_document(document_id)
        if document is None:
            raise SourceSpanNotFound(document_id, sequence)

        saved_source_spans = self.store.get_source_span(document_id, sequence)

        if saved_source_spans is None:
            raise SourceSpanNotFound(document_id, sequence)

        return saved_source_spans

    # 保存的引用确实出现在该片段中
    def _check_evidence(self, span: SourceSpan, evidence_quote: str) -> None:
        if evidence_quote not in span["body"]:
            raise EvidenceNotInSourceSpan(
                "Evidence quote was not found in the source span"
            )

    def confirm(self, fact_id: int) -> FactDraft:
        fact = self.store.get_fact(fact_id)
        if fact is None:
            raise FactNotFound(fact_id)
        if fact.status == "rejected":
            raise InvalidFactTransition(
                "Rejected facts must be edited before confirmation"
            )

        if fact.status == "confirmed":
            return fact

        confirmed = self.store.confirm_fact(fact_id)
        if confirmed is None:
            raise RuntimeError("Fact could not be confirmed")
        return confirmed

    def edit(self, fact_id: int, claim: str) -> FactDraft:
        fact = self.store.get_fact(fact_id)
        if fact is None:
            raise FactNotFound(fact_id)

        edited_fact = self.store.edit_fact(fact_id, claim)
        if edited_fact is None:
            raise RuntimeError("Fact could not be edited")
        return edited_fact

    def reject(self, fact_id: int) -> FactDraft:
        fact = self.store.get_fact(fact_id)
        if fact is None:
            raise FactNotFound(fact_id)

        if fact.status == "rejected":
            return fact

        rejected = self.store.reject_fact(fact_id)
        if rejected is None:
            raise RuntimeError("Fact could not be rejected")
        return rejected

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
            run_id = self.store.save_model_fact_run(
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

        fact_id = self.store.save_fact(
            document_id, output.claim, output.evidence_quote, span["sequence"], run_id
        )

        fact = self.store.get_fact(fact_id)

        if fact is None:
            raise RuntimeError("Saved fact could not be read")

        return fact
