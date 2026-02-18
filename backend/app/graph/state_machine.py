import logging
from typing import Optional, Dict, Any
from app.core.session import ConversationState, SessionData

logger = logging.getLogger(__name__)


class StateMachine:
    """Deterministic state machine controller"""
    
    def __init__(self):
        # Define valid state transitions
        self.transitions = {
            ConversationState.GREETING: [ConversationState.CONSENT],
            ConversationState.CONSENT: [ConversationState.CUSTOMER_ID, ConversationState.GREETING],
            ConversationState.CUSTOMER_ID: [ConversationState.AMOUNT, ConversationState.CONSENT],
            ConversationState.AMOUNT: [ConversationState.NEED_DOCS, ConversationState.CUSTOMER_ID],
            ConversationState.NEED_DOCS: [ConversationState.DOC_UPLOAD, ConversationState.AMOUNT],
            ConversationState.DOC_UPLOAD: [ConversationState.OCR_CONFIRM, ConversationState.DOC_UPLOAD],
            ConversationState.OCR_CONFIRM: [ConversationState.UNDERWRITING, ConversationState.DOC_UPLOAD],
            ConversationState.UNDERWRITING: [ConversationState.DECISION],
            ConversationState.DECISION: [ConversationState.COMPLETED],
            ConversationState.COMPLETED: []
        }
    
    def get_next_state(self, current_state: ConversationState, action: str, context: Dict[str, Any]) -> Optional[ConversationState]:
        """
        Determine next state based on current state and action
        
        Args:
            current_state: Current conversation state
            action: Action taken (e.g., "consent_given", "amount_provided")
            context: Additional context (slots, etc.)
            
        Returns:
            Next state or None if invalid transition
        """
        logger.info(f"State transition request: {current_state} -> {action}")
        
        if current_state == ConversationState.GREETING:
            if action == "greeting_completed":
                return ConversationState.CONSENT
        
        elif current_state == ConversationState.CONSENT:
            if action == "consent_given":
                return ConversationState.CUSTOMER_ID
            elif action == "consent_denied":
                return ConversationState.GREETING
        
        elif current_state == ConversationState.CUSTOMER_ID:
            if action == "customer_id_provided":
                return ConversationState.AMOUNT
            elif action == "correction":
                return ConversationState.CONSENT
        
        elif current_state == ConversationState.AMOUNT:
            if action == "amount_provided":
                return ConversationState.NEED_DOCS
            elif action == "correction":
                return ConversationState.CUSTOMER_ID
        
        elif current_state == ConversationState.NEED_DOCS:
            if action == "docs_acknowledged":
                return ConversationState.DOC_UPLOAD
            elif action == "correction":
                return ConversationState.AMOUNT
        
        elif current_state == ConversationState.DOC_UPLOAD:
            if action == "docs_uploaded":
                return ConversationState.OCR_CONFIRM
            elif action == "retry_upload":
                return ConversationState.DOC_UPLOAD
        
        elif current_state == ConversationState.OCR_CONFIRM:
            if action == "ocr_confirmed":
                return ConversationState.UNDERWRITING
            elif action == "ocr_rejected":
                return ConversationState.DOC_UPLOAD
        
        elif current_state == ConversationState.UNDERWRITING:
            if action == "underwriting_completed":
                return ConversationState.DECISION
        
        elif current_state == ConversationState.DECISION:
            if action == "decision_delivered":
                return ConversationState.COMPLETED
        
        logger.warning(f"Invalid transition: {current_state} -> {action}")
        return None
    
    def can_rewind(self, current_state: ConversationState) -> bool:
        """Check if state can be rewound"""
        non_rewindable = [
            ConversationState.UNDERWRITING,
            ConversationState.DECISION,
            ConversationState.COMPLETED
        ]
        return current_state not in non_rewindable
    
    def validate_transition(self, from_state: ConversationState, to_state: ConversationState) -> bool:
        """Validate if transition is allowed"""
        allowed_transitions = self.transitions.get(from_state, [])
        return to_state in allowed_transitions


state_machine = StateMachine()
