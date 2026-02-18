import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.session import session_manager
from app.mock_services import mock_underwriting_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/underwriting", tags=["underwriting"])


class UnderwritingResponse(BaseModel):
    session_id: str
    decision: str
    reason: str
    approved_amount: float
    interest_rate: float


@router.post("/trigger/{session_id}", response_model=UnderwritingResponse)
async def trigger_underwriting(session_id: str):
    """
    Manually trigger underwriting process
    
    Used for testing or explicit underwriting requests
    """
    try:
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Validate required slots
        loan_amount = session.get_slot("loan_amount")
        customer_id = session.get_slot("customer_id")
        ocr_data = session.get_slot("ocr_data")
        
        if not all([loan_amount, customer_id, ocr_data]):
            raise HTTPException(
                status_code=400,
                detail="Missing required information for underwriting"
            )
        
        # Perform underwriting
        result = await mock_underwriting_service.assess_loan(
            customer_id=customer_id,
            loan_amount=loan_amount,
            income_data=ocr_data.get("salary_slip", {}).get("data", {})
        )
        
        session.update_slot("underwriting_result", result)
        session.update_slot("decision", result["decision"])
        await session_manager.update_session(session)
        
        return UnderwritingResponse(
            session_id=session_id,
            decision=result["decision"],
            reason=result["reason"],
            approved_amount=result["approved_amount"],
            interest_rate=result["interest_rate"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in underwriting: {e}")
        raise HTTPException(status_code=500, detail="Underwriting failed")
