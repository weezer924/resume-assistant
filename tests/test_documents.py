from collections.abc import Iterator
from pathlib import Path
from typing import cast

import pytest
from fastapi.testclient import TestClient

from app.database import SqliteFactStore
from app.dependencies import get_store
from app.main import app


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    app.dependency_overrides[get_store] = lambda: SqliteFactStore(
        str(tmp_path / "test.db")
    )
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_import_document_with_file(client: TestClient):
    sample = Path(__file__).parent / "fixtures" / "sample_resume.md"

    files = {"file": ("sample_resume.md", sample.read_bytes(), "text/markdown")}

    response = client.post(
        "/documents/import",
        files=files,
    )
    assert response.status_code == 200
    spans = cast(list[object], response.json()["spans"])
    first = cast(dict[str, object], spans[0])
    assert first["section"] == "職務経歴書"
    assert len(spans) == 9


def test_import_document_no_file(client: TestClient):
    response = client.post("/documents/import")

    assert response.status_code == 422
