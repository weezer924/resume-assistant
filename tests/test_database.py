import sqlite3
from pathlib import Path
from typing import cast

import pytest

from app.database import SqliteStore
from app.schema import Document, Job, ModelJobRequirementOutput, SourceSpan

DOCUMENT_ID_1 = "doc1"
DOCUMENT_ID_2 = "doc2"


def dummy_source_span_1() -> SourceSpan:
    return {
        "section": "example_section_1",
        "level": 1,
        "body": "example_body_1",
        "sequence": 1,
    }


def dummy_source_span_2() -> SourceSpan:
    return {
        "section": "example_section_2",
        "level": 1,
        "body": "example_body_2",
        "sequence": 2,
    }


def dummy_source_span_3() -> SourceSpan:
    return {
        "section": "example_section_3",
        "level": 1,
        "body": "example_body_3",
        "sequence": 1,
    }


@pytest.fixture
def store(tmp_path: Path) -> SqliteStore:
    store = SqliteStore(str(tmp_path / "test.db"))
    store.save_document(
        Document(
            document_id=DOCUMENT_ID_1,
            filename="a.md",
            content="# example_section_1\nexample_body_1\n# example_section_2\nexample_body_2",
        )
    )
    store.save_document(
        Document(
            document_id=DOCUMENT_ID_2,
            filename="b.md",
            content="# example_section_3\nexample_body_3",
        )
    )
    return store


def test_get_source_span_not_found(store: SqliteStore):
    source_span = store.get_source_span(DOCUMENT_ID_1, 999)
    assert source_span is None


def test_source_span_sequence_is_not_mixed(store: SqliteStore):
    source_span_1 = dummy_source_span_1()
    source_span_2 = dummy_source_span_2()

    store.save_source_span(DOCUMENT_ID_1, source_span_1)
    store.save_source_span(DOCUMENT_ID_1, source_span_2)

    retrieved_source_span = store.get_source_span(DOCUMENT_ID_1, 1)

    assert retrieved_source_span == source_span_1


def test_source_span_retrieval_by_sequence(store: SqliteStore):
    source_span_1 = dummy_source_span_1()
    source_span_3 = dummy_source_span_3()

    store.save_source_span(DOCUMENT_ID_1, source_span_1)
    store.save_source_span(DOCUMENT_ID_2, source_span_3)

    retrieved_source_span_1 = store.get_source_span(DOCUMENT_ID_1, 1)
    retrieved_source_span_3 = store.get_source_span(DOCUMENT_ID_2, 1)

    assert retrieved_source_span_1 != retrieved_source_span_3
    assert retrieved_source_span_1 == source_span_1
    assert retrieved_source_span_3 == source_span_3


def test_save_document_with_spans(store: SqliteStore):

    invalid_span = {
        "section": "Invalid",
        "level": 1,
        "body": None,
        "sequence": 2,
    }

    document = Document(
        document_id="error-document",
        filename="error-document.md",
        content="synthetic content",
    )
    spans = [dummy_source_span_1(), cast(SourceSpan, cast(object, invalid_span))]

    with pytest.raises(sqlite3.IntegrityError):
        store.save_document_with_spans(document, spans)

    assert store.get_document(document.document_id) is None
    assert store.get_source_span(document.document_id, 1) is None


def test_save_job(store: SqliteStore):
    job = Job(id="job-1", source_text="We need a python engineer")

    store.save_job(job)
    saved_job = store.get_job(job.id)

    assert saved_job == job


def test_save_job_requirement(store: SqliteStore):
    job = Job(id="job-1", source_text="We need a python engineer")
    store.save_job(job)

    requirements = [
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

    requirement_ids = store.save_job_requirements(job.id, requirements)

    saved = store.get_job_requirements(job.id)

    assert len(saved) == len(requirement_ids) == 2
    assert saved[0].id == requirement_ids[0]
    assert saved[1].id == requirement_ids[1]
    assert saved[0].id != saved[1].id

    for actual, expected in zip(saved, requirements):
        assert actual.job_id == job.id
        assert actual.model_dump(exclude={"id", "job_id"}) == expected.model_dump()
