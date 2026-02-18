import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import asyncio
from uuid import uuid4

logger = logging.getLogger(__name__)


class ConversationState(str, Enum):
    """State machine states"""
    GREETING = "GREETING"
    CONSENT = "CONSENT"
    CUSTOMER_ID = "CUSTOMER_ID"
    AMOUNT = "AMOUNT"
    NEED_DOCS = "NEED_DOCS"
    DOC_UPLOAD = "DOC_UPLOAD"
    OCR_CONFIRM = "OCR_CONFIRM"
    UNDERWRITING = "UNDERWRITING"
    DECISION = "DECISION"
    COMPLETED = "COMPLETED"


class SessionData:
    """Session state container"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.current_state = ConversationState.GREETING
        self.history: list[Dict[str, str]] = []
        
        # Slots
        self.slots: Dict[str, Any] = {
            "consent": None,
            "customer_id": None,
            "loan_amount": None,
            "documents": {},
            "ocr_data": {},
            "underwriting_result": None,
            "decision": None
        }
        
        # State history for rewind capability
        self.state_history: list[ConversationState] = [ConversationState.GREETING]
    
    def update_slot(self, key: str, value: Any):
        """Update a slot value"""
        self.slots[key] = value
        self.updated_at = datetime.utcnow()
    
    def get_slot(self, key: str) -> Any:
        """Get slot value"""
        return self.slots.get(key)
    
    def add_message(self, role: str, content: str):
        """Add message to conversation history"""
        self.history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.updated_at = datetime.utcnow()
    
    def transition_state(self, new_state: ConversationState):
        """Transition to new state"""
        if new_state != self.current_state:
            self.state_history.append(new_state)
            self.current_state = new_state
            self.updated_at = datetime.utcnow()
            logger.info(f"Session {self.session_id} transitioned to {new_state}")
    
    def rewind_state(self) -> bool:
        """Rewind to previous state"""
        if len(self.state_history) > 1:
            self.state_history.pop()
            self.current_state = self.state_history[-1]
            self.updated_at = datetime.utcnow()
            logger.info(f"Session {self.session_id} rewound to {self.current_state}")
            return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize session to dictionary"""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "current_state": self.current_state.value,
            "history": self.history,
            "slots": self.slots,
            "state_history": [s.value for s in self.state_history]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionData":
        """Deserialize session from dictionary"""
        session = cls(data["session_id"])
        session.created_at = datetime.fromisoformat(data["created_at"])
        session.updated_at = datetime.fromisoformat(data["updated_at"])
        session.current_state = ConversationState(data["current_state"])
        session.history = data["history"]
        session.slots = data["slots"]
        session.state_history = [ConversationState(s) for s in data["state_history"]]
        return session


class SessionManager:
    """In-memory session manager with optional Redis backend"""
    
    def __init__(self):
        self.sessions: Dict[str, SessionData] = {}
        self.lock = asyncio.Lock()
    
    async def create_session(self) -> SessionData:
        """Create new session"""
        session_id = str(uuid4())
        session = SessionData(session_id)
        
        async with self.lock:
            self.sessions[session_id] = session
        
        logger.info(f"Created session {session_id}")
        return session
    
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """Retrieve session by ID"""
        async with self.lock:
            session = self.sessions.get(session_id)
            if session:
                # Check expiry
                if datetime.utcnow() - session.updated_at > timedelta(seconds=3600):
                    del self.sessions[session_id]
                    logger.info(f"Session {session_id} expired")
                    return None
            return session
    
    async def update_session(self, session: SessionData):
        """Update existing session"""
        async with self.lock:
            self.sessions[session.session_id] = session
    
    async def delete_session(self, session_id: str):
        """Delete session"""
        async with self.lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.info(f"Deleted session {session_id}")
    
    async def cleanup_expired(self):
        """Remove expired sessions"""
        async with self.lock:
            now = datetime.utcnow()
            expired = [
                sid for sid, sess in self.sessions.items()
                if now - sess.updated_at > timedelta(seconds=3600)
            ]
            for sid in expired:
                del self.sessions[sid]
            if expired:
                logger.info(f"Cleaned up {len(expired)} expired sessions")


# Global session manager
session_manager = SessionManager()
