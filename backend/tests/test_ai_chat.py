# backend/tests/test_ai_chat.py

import os
import pytest
from fastapi.testclient import TestClient
from app.main import app, SESSION_MEMORY

client = TestClient(app)

HF_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")


@pytest.mark.skipif(not HF_TOKEN, reason="HuggingFace token not set")
def test_chat_ai_response():
    """
    Chat should return a non-empty LLM response
    and should not be the old echo format.
    """
    payload = {
        "message": "Hello",
        "session_id": "ai-test-1",
    }

    response = client.post("/chat", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["reply"], "AI response should not be empty"
    # sanity: old echo text should not appear
    assert "You said:" not in data["reply"]


@pytest.mark.skipif(not HF_TOKEN, reason="HuggingFace token not set")
def test_session_memory_retains_conversation():
    """
    Session memory should retain messages across multiple calls.
    """
    sid = "ai-test-2"

    client.post("/chat", json={"message": "Hello", "session_id": sid})
    client.post("/chat", json={"message": "What do you do?", "session_id": sid})

    assert sid in SESSION_MEMORY
    state = SESSION_MEMORY[sid]
    # At least 2 user + 2 bot messages
    assert len(state.messages) >= 4
