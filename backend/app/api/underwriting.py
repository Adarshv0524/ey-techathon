# app/api/underwriting.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app import mock_services
from app.underwriting import evaluate_application

router = APIRouter()


class UnderwriteRequest(BaseModel):
    customer_id: str
    requested_amount: int


class UnderwriteResponse(BaseModel):
    decision: str
    approved_amount: int
    requested_amount: int
    reason: str
    metadata: dict


@router.post("/underwrite/simulate", response_model=UnderwriteResponse)
def simulate(payload: UnderwriteRequest):
    profile = mock_services.get_crm_profile(payload.customer_id)
    if not profile:
        raise HTTPException(404, "Customer not found")

    bureau = mock_services.get_bureau_report(payload.customer_id)
    if not bureau:
        raise HTTPException(404, "Bureau report not found")

    decision = evaluate_application(profile, bureau, payload.requested_amount)
    decision["requested_amount"] = payload.requested_amount
    return UnderwriteResponse(**decision)
