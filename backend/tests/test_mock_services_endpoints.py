# backend/tests/test_mock_services_endpoints.py

from fastapi.testclient import TestClient
from app.main import app
from app import mock_services

client = TestClient(app)


def test_get_crm_success():
    # Ensure our fixture customer exists
    customer_id = "CUST001"
    assert mock_services.get_crm_profile(customer_id) is not None

    resp = client.get(f"/mock/crm/{customer_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["customer_id"] == customer_id
    assert "monthly_income" in data


def test_get_crm_not_found():
    resp = client.get("/mock/crm/UNKNOWN")
    assert resp.status_code == 404


def test_get_bureau_success():
    customer_id = "CUST001"
    assert mock_services.get_bureau_report(customer_id) is not None

    resp = client.get(f"/mock/bureau/{customer_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["customer_id"] == customer_id
    assert "credit_score" in data


def test_get_bureau_not_found():
    resp = client.get("/mock/bureau/UNKNOWN")
    assert resp.status_code == 404


def test_consent_endpoint_records_entry():
    payload = {
        "customer_id": "CUST001",
        "consent_text": "I agree to processing my data for loan evaluation.",
    }

    resp = client.post("/consent", json=payload)
    assert resp.status_code == 200

    data = resp.json()
    assert data["customer_id"] == "CUST001"
    assert data["channel"] == "chat"
    assert "timestamp" in data
