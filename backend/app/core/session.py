from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class LoanStage(str, Enum):
    GREETING = "GREETING"
    CONSENT = "CONSENT"
    COLLECT_CUSTOMER_ID = "COLLECT_CUSTOMER_ID"
    COLLECT_AMOUNT = "COLLECT_AMOUNT"
    CRM_CHECK = "CRM_CHECK"
    BUREAU_CHECK = "BUREAU_CHECK"
    UNDERWRITING = "UNDERWRITING"
    DECISION = "DECISION"
    ESCALATED = "ESCALATED"
    COMPLETED = "COMPLETED"


class ChatMessage(BaseModel):
    role: str
    type: str
    content: str


class LoanState(BaseModel):
    session_id: str
    stage: LoanStage = LoanStage.GREETING

    messages: List[ChatMessage] = Field(default_factory=list)

    # Slots / Memory
    slots: Dict = Field(default_factory=dict)

    customer_id: Optional[str] = None
    requested_amount: Optional[int] = None

    crm_profile: Optional[Dict] = None
    bureau_report: Optional[Dict] = None
    underwriting_result: Optional[Dict] = None


# In-memory session store (Short-term memory)
sessions: Dict[str, LoanState] = {}


def get_session_state(session_id: str) -> LoanState:
    if session_id not in sessions:
        sessions[session_id] = LoanState(session_id=session_id)
    return sessions[session_id]
