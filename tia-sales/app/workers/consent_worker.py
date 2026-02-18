import logging
from typing import Dict, Any
from app.core.session import SessionData
from app.graph.slot_filler import slot_filler
from app.graph.state_machine import state_machine

logger = logging.getLogger(__name__)


class ConsentWorker:
    """Handles consent collection"""
    
    async def process(self, user_message: str, session: SessionData) -> Dict[str, Any]:
        """
        Process consent-related message
        
        Returns:
            Worker result with response and state updates
        """
        # Check if consent already given
        if session.get_slot("consent") is not None:
            response = "I see you've already provided consent. Let's continue."
            next_state = state_machine.get_next_state(
                session.current_state,
                "consent_given",
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
        
        # Extract consent from message
        consent_value = await slot_filler.extract_consent(user_message)
        
        if consent_value is True:
            session.update_slot("consent", True)
            
            response = "Thank you for your consent. To proceed, I'll need your Customer ID. Could you please provide it?"
            
            next_state = state_machine.get_next_state(
                session.current_state,
                "consent_given",
                {}
            )
            if next_state:
                session.transition_state(next_state)
            
            return {
                "response": response,
                "state_changed": True,
                "new_state": session.current_state.value,
                "slots_updated": {"consent": True}
            }
        
        elif consent_value is False:
            session.update_slot("consent", False)
            
            response = "I understand. Without your consent, I won't be able to proceed with the loan application. If you change your mind, feel free to reach out. Have a great day!"
            
            next_state = state_machine.get_next_state(
                session.current_state,
                "consent_denied",
                {}
            )
            if next_state:
                session.transition_state(next_state)
            
            return {
                "response": response,
                "state_changed": True,
                "new_state": session.current_state.value,
                "slots_updated": {"consent": False}
            }
        
        else:
            # Consent not clear, ask again
            response = "I need your explicit consent to proceed with collecting your information for the loan application. Do you agree to share your details? Please respond with 'yes' or 'no'."
            
            return {
                "response": response,
                "state_changed": False,
                "new_state": session.current_state.value,
                "slots_updated": {}
            }


consent_worker = ConsentWorker()
