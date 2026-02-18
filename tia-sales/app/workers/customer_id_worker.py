import logging
from typing import Dict, Any
from app.core.session import SessionData
from app.graph.slot_filler import slot_filler
from app.graph.state_machine import state_machine
from app.mock_services import mock_customer_service

logger = logging.getLogger(__name__)


class CustomerIdWorker:
    """Handles customer ID collection and validation"""
    
    async def process(self, user_message: str, session: SessionData) -> Dict[str, Any]:
        """Process customer ID input"""
        
        # Extract customer ID
        customer_id = await slot_filler.extract_customer_id(user_message)
        
        if customer_id:
            # Validate customer ID
            is_valid = await mock_customer_service.validate_customer_id(customer_id)
            
            if is_valid:
                session.update_slot("customer_id", customer_id)
                
                response = f"Great! I've verified your Customer ID ({customer_id}). Now, how much loan amount are you looking for?"
                
                next_state = state_machine.get_next_state(
                    session.current_state,
                    "customer_id_provided",
                    {}
                )
                if next_state:
                    session.transition_state(next_state)
                
                return {
                    "response": response,
                    "state_changed": True,
                    "new_state": session.current_state.value,
                    "slots_updated": {"customer_id": customer_id}
                }
            else:
                response = f"I couldn't verify the Customer ID '{customer_id}'. Please check and provide the correct ID."
                
                return {
                    "response": response,
                    "state_changed": False,
                    "new_state": session.current_state.value,
                    "slots_updated": {}
                }
        
        else:
            response = "I couldn't find a valid Customer ID in your message. Please provide your Customer ID in the format 'CUST' followed by digits (e.g., CUST123456)."
            
            return {
                "response": response,
                "state_changed": False,
                "new_state": session.current_state.value,
                "slots_updated": {}
            }


customer_id_worker = CustomerIdWorker()
