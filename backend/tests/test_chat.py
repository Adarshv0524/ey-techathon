# backend/tests/test_chat.py

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """
    Verify /health endpoint works and returns expected payload.
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_chat_echo_basic():
    """
    Verify /chat echoes back the message with expected format.
    """
    payload = {
        "message": "Hello TIA!",
        "session_id": "test-session-123",
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 200

    data = response.json()
    # Check that reply contains our message in the expected format
    assert data["reply"] == "You said: Hello TIA!"
    assert data["session_id"] == "test-session-123"


def test_chat_missing_session_id():
    """
    session_id should be optional and still return a valid response.
    """
    payload = {
        "message": "No session id here",
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["reply"] == "You said: No session id here"
    # session_id should be present in response but None
    assert "session_id" in data
    assert data["session_id"] is None


def test_chat_validation_error_on_empty_message():
    """
    If message field is missing entirely, FastAPI should return 422.
    """
    payload = {
        "session_id": "whatever"
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 422  # Unprocessable Entity
