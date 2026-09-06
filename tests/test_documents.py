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
    response = client.post(
        "/documents/import",
        files={"file": ("a.md", b"Jack\n# Experience\nfoo", "text/markdown")},
    )

    assert response.status_code == 200
    spans = cast(list[object], response.json()["spans"])
    assert len(spans) == 2


def test_import_document_no_file(client: TestClient):
    response = client.post("/documents/import")

    assert response.status_code == 422
