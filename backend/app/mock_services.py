# backend/app/mock_services.py

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

# --- In-memory stores (for hackathon demo) --- #

MOCK_CUSTOMERS: Dict[str, Dict[str, Any]] = {
    "CUST001": {
        "customer_id": "CUST001",
        "name": "Adarsh Verma",
        "segment": "salaried",
        "monthly_income": 60000,
        "existing_emi": 5000,
        "pre_approved_limit": 500000,
        "pan": "ABCDE1234F",
    },
    "CUST002": {
        "customer_id": "CUST002",
        "name": "Neha Verma",
        "segment": "salaried",
        "monthly_income": 40000,
        "existing_emi": 8000,
        "pre_approved_limit": 200000,
        "pan": "PQRSX5678Z",
    },
    "CUST003": {
        "customer_id": "CUST003",
        "name": "Kas Kla",
        "segment": "self-employed",
        "monthly_income": 30000,
        "existing_emi": 10000,
        "pre_approved_limit": 100000,
        "pan": "LMNOP9876K",
    },
}

MOCK_BUREAU: Dict[str, Dict[str, Any]] = {
    "CUST001": {
        "customer_id": "CUST001",
        "credit_score": 780,
        "delinquency_flags": [],
    },
    "CUST002": {
        "customer_id": "CUST002",
        "credit_score": 710,
        "delinquency_flags": [],
    },
    "CUST003": {
        "customer_id": "CUST003",
        "credit_score": 620,
        "delinquency_flags": ["high_delinquency_risk"],
    },
}

CONSENT_LOG: List[Dict[str, Any]] = []


# --- Helper functions used by endpoints & agents --- #

def get_crm_profile(customer_id: str) -> Optional[Dict[str, Any]]:
    return MOCK_CUSTOMERS.get(customer_id)


def get_bureau_report(customer_id: str) -> Optional[Dict[str, Any]]:
    return MOCK_BUREAU.get(customer_id)


def record_consent(customer_id: str, consent_text: str, channel: str = "chat") -> Dict[str, Any]:
    entry = {
        "customer_id": customer_id,
        "consent_text": consent_text,
        "channel": channel,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    CONSENT_LOG.append(entry)
    return entry
