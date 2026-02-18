# app/api/consent.py

from fastapi import APIRouter
from pydantic import BaseModel
from app import mock_services

router = APIRouter()


class ConsentRequest(BaseModel):
    customer_id: str
    consent_text: str


class ConsentResponse(BaseModel):
    customer_id: str
    timestamp: str
    channel: str


@router.post("/consent", response_model=ConsentResponse)
def consent(payload: ConsentRequest):
    entry = mock_services.record_consent(
        payload.customer_id,
        payload.consent_text,
        channel="chat",
    )
    return ConsentResponse(**entry)
