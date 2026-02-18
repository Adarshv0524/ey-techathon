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
    Verify /chat now returns a real AI response and still handles the session_id.
    """
    # ADD THESE LINES:
    payload = {
        "message": "Hello TIA!",
        "session_id": "test-session-123",
    }
    # END ADDED LINES
    
    response = client.post("/chat", json=payload)
    assert response.status_code == 200

    # ... rest of the function ...


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
    
    # 1. NEW ASSERTION: Check that the reply is a real AI response (not an echo)
    assert data["reply"], "AI response should not be empty."
    assert "You said:" not in data["reply"], "Reply should be an AI response, not an echo."
    
    # 2. NEW ASSERTION: The session ID should default to "default" 
    # (as per your main.py logic: sid = payload.session_id or "default")
    assert data["session_id"] == "default", "The response should return the 'default' session ID when none is provided."

def test_chat_validation_error_on_empty_message():
    """
    If message field is missing entirely, FastAPI should return 422.
    """
    payload = {
        "session_id": "whatever"
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 422  # Unprocessable Entity
