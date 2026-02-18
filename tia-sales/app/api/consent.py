import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.session import session_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/consent", tags=["consent"])


class ConsentRequest(BaseModel):
    session_id: str
    consent: bool


class ConsentResponse(BaseModel):
    session_id: str
    consent_recorded: bool
    message: str


@router.post("/record", response_model=ConsentResponse)
async def record_consent(request: ConsentRequest):
    """
    Explicit consent recording endpoint
    
    Allows frontend to record consent separately
    """
    try:
        session = await session_manager.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session.update_slot("consent", request.consent)
        await session_manager.update_session(session)
        
        message = "Consent recorded successfully" if request.consent else "Consent declined"
        
        return ConsentResponse(
            session_id=session.session_id,
            consent_recorded=True,
            message=message
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording consent: {e}")
        raise HTTPException(status_code=500, detail="Failed to record consent")
