import logging
from typing import Dict, Any, Optional
from app.core.session import SessionData, ConversationState
from app.graph.state_machine import state_machine
from app.graph.slot_filler import slot_filler
from app.workers.consent_worker import consent_worker
from app.workers.customer_id_worker import customer_id_worker
from app.workers.amount_worker import amount_worker
from app.workers.document_worker import document_worker
from app.workers.underwriting_worker import underwriting_worker
from app.workers.decision_worker import decision_worker

logger = logging.getLogger(__name__)


class DialogueManager:
    """Orchestrates conversation flow and delegates to workers"""
    
    async def process_task_action(self, user_message: str, session: SessionData) -> Dict[str, Any]:
        """
        Process task-oriented user message
        
        Returns:
            {
                "response": str,
                "state_changed": bool,
                "new_state": str,
                "slots_updated": dict
            }
        """
        current_state = session.current_state
        logger.info(f"Processing task action in state: {current_state}")
        
        # Check for correction intent
        correction = await slot_filler.detect_correction(user_message)
        if correction and state_machine.can_rewind(current_state):
            session.rewind_state()
            return {
                "response": "I understand you want to correct something. Let's go back.",
                "state_changed": True,
                "new_state": session.current_state.value,
                "slots_updated": {}
            }
        
        # Route to appropriate worker based on state
        if current_state == ConversationState.GREETING:
            return await self._handle_greeting(user_message, session)
        
        elif current_state == ConversationState.CONSENT:
            return await consent_worker.process(user_message, session)
        
        elif current_state == ConversationState.CUSTOMER_ID:
            return await customer_id_worker.process(user_message, session)
        
        elif current_state == ConversationState.AMOUNT:
            return await amount_worker.process(user_message, session)
        
        elif current_state == ConversationState.NEED_DOCS:
            return await document_worker.process_need_docs(user_message, session)
        
        elif current_state == ConversationState.DOC_UPLOAD:
            return await document_worker.process_upload(user_message, session)
        
        elif current_state == ConversationState.OCR_CONFIRM:
            return await document_worker.process_confirm(user_message, session)
        
        elif current_state == ConversationState.UNDERWRITING:
            return await underwriting_worker.process(user_message, session)
        
        elif current_state == ConversationState.DECISION:
            return await decision_worker.process(user_message, session)
        
        elif current_state == ConversationState.COMPLETED:
            return {
                "response": "Your loan application has been completed. Is there anything else I can help you with?",
                "state_changed": False,
                "new_state": current_state.value,
                "slots_updated": {}
            }
        
        return {
            "response": "I'm not sure how to proceed. Could you please clarify?",
            "state_changed": False,
            "new_state": current_state.value,
            "slots_updated": {}
        }
    
    async def _handle_greeting(self, user_message: str, session: SessionData) -> Dict[str, Any]:
        """Handle initial greeting state"""
        response = "Hello! Welcome to TIA Personal Loans. I'm here to help you with your loan application. Shall we begin?"
        
        next_state = state_machine.get_next_state(
            session.current_state,
            "greeting_completed",
            {}
        )
        
        if next_state:
            session.transition_state(next_state)
        
        return {
            "response": response,
            "state_changed": True,
            "new_state": session.current_state.value,
            "slots_updated": {}
        }


dialogue_manager = DialogueManager()
