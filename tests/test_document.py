from typing import cast

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_import_document_with_file():
    response = client.post(
        "/documents/import",
        files={"file": ("a.md", b"Jack\n# Experience\nfoo", "text/markdown")},
    )
    assert response.status_code == 200
    spans = cast(list[object], response.json()["spans"])
    assert len(spans) == 2


def test_import_document_no_file():
    response = client.post("/documents/import")
    assert response.status_code == 422
