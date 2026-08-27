import pytest
from fastapi.testclient import TestClient
import pymupdf as fitz
from app.main import app

@pytest.fixture(scope="function")
def client():
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def make_pdf():
    def _generator(pages_text: list[str]) -> bytes:
        doc = fitz.open()
        for text in pages_text:
            page = doc.new_page()
            page.insert_text(fitz.Point(40, 60), text, fontsize=10)
        data = doc.tobytes()
        doc.close()
        return data
    return _generator
