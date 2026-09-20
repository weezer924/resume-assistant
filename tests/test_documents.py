from collections.abc import Iterator
from pathlib import Path
from typing import cast

import pytest
from fastapi.testclient import TestClient

from app.database import SqliteFactStore
from app.dependencies import get_store
from app.main import app
from app.schema import SourceSpan


def parsing_should_not_run(_content: str) -> list[SourceSpan]:
    raise AssertionError("Should use persisted SourceSpans")


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    app.dependency_overrides[get_store] = lambda: SqliteFactStore(
        str(tmp_path / "test.db")
    )
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_import_document_with_file(client: TestClient, tmp_path: Path):
    sample = Path(__file__).parent / "fixtures" / "sample_resume.md"

    files = {"file": ("sample_resume.md", sample.read_bytes(), "text/markdown")}

    response = client.post(
        "/documents/import",
        files=files,
    )

    assert response.status_code == 200

    spans: list[SourceSpan] = cast(list[SourceSpan], response.json()["spans"])
    first = spans[0]
    assert first["section"] == "職務経歴書"
    assert len(spans) == 7

    document_id = cast(str, response.json()["document_id"])
    store = SqliteFactStore(str(tmp_path / "test.db"))
    saved_span = store.get_source_span(document_id, first["sequence"])
    assert saved_span == first


def test_import_document_no_file(client: TestClient):
    response = client.post("/documents/import")

    assert response.status_code == 422


def test_import_document_empty_file(client: TestClient):
    files = {"file": ("empty.md", b"", "text/markdown")}

    response = client.post(
        "/documents/import",
        files=files,
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Uploaded file is empty"


def test_import_document_non_utf8_file(client: TestClient):
    files = {"file": ("non_utf8.md", b"\xff", "text/markdown")}

    response = client.post(
        "/documents/import",
        files=files,
    )

    assert response.status_code == 422
    assert (
        response.json()["detail"] == "Uploaded file must be a UTF-8 encoded text file"
    )


def test_import_document_file_with_only_empty_lines(client: TestClient):
    files = {"file": ("only_empty_lines.md", b"\n\n\n", "text/markdown")}

    response = client.post(
        "/documents/import",
        files=files,
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Uploaded file is empty"
