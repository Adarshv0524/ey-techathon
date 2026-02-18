# backend/tests/test_underwriting_endpoint.py

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_underwrite_approve_high_score():
    """
    High-score customer with reasonable request should be approved.
    """
    payload = {
        "customer_id": "CUST001",  # score 780, income 60000
        "requested_amount": 200000,
    }

    resp = client.post("/underwrite/simulate", json=payload)
    assert resp.status_code == 200

    data = resp.json()
    assert data["decision"] in ("approve", "need_docs")
    assert data["approved_amount"] > 0
    assert data["requested_amount"] == 200000
    assert "reason" in data


def test_underwrite_reject_low_score():
    """
    Low-score customer CUST003 should be rejected under rules (score 620 < 650).
    """
    payload = {
        "customer_id": "CUST003",  # score 620
        "requested_amount": 100000,
    }

    resp = client.post("/underwrite/simulate", json=payload)
    assert resp.status_code == 200

    data = resp.json()
    assert data["decision"] == "reject"
    assert data["approved_amount"] == 0
    assert "below minimum eligibility" in data["reason"]
