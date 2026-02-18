# backend/tests/test_chat_underwriting_flow.py

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_chat_underwriting_from_message():
    """
    The /chat endpoint should be able to run an underwriting simulation
    when the user message contains a customer id and amount.
    This path should not require the LLM.
    """
    payload = {
        "message": "Please check loan eligibility for CUST001 amount 200000",
        "session_id": "uw-chat-test-1",
    }

    resp = client.post("/chat", json=payload)
    assert resp.status_code == 200

    data = resp.json()
    reply = data["reply"]

    # Basic sanity checks
    assert "Loan eligibility decision for CUST001" in reply
    assert "Requested amount: ₹200,000" in reply
    # Decision could be APPROVE or NEED_DOCS depending on rules, but content must be there
    assert "Reason:" in reply
