# backend/tests/test_faq_endpoint.py

import os
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

HF_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")


@pytest.mark.skipif(not HF_TOKEN, reason="HuggingFace token not set")
def test_faq_query_basic():
    """
    Ask a simple policy question and ensure we get an answer + snippets.
    """
    payload = {
        "question": "What is the maximum personal loan tenure?"
    }

    resp = client.post("/faq/query", json=payload)
    assert resp.status_code == 200

    data = resp.json()
    assert "answer" in data
    assert "snippets" in data
    assert isinstance(data["snippets"], list)
    # At least one snippet should be returned for this question
    assert len(data["snippets"]) >= 1
