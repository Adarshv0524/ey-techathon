import logging
from typing import Dict, Any
from app.core.session import SessionData
from app.graph.state_machine import state_machine
from app.mock_services import mock_underwriting_service

logger = logging.getLogger(__name__)


class UnderwritingWorker:
    """Handles loan underwriting simulation"""
    
    async def process(self, user_message: str, session: SessionData) -> Dict[str, Any]:
        """Process underwriting"""
        
        # Gather all required data
        loan_amount = session.get_slot("loan_amount")
        customer_id = session.get_slot("customer_id")
        ocr_data = session.get_slot("ocr_data")
        
        # Perform underwriting
        underwriting_result = await mock_underwriting_service.assess_loan(
            customer_id=customer_id,
            loan_amount=loan_amount,
            income_data=ocr_data.get("salary_slip", {}).get("data", {})
        )
        
        session.update_slot("underwriting_result", underwriting_result)
        
        response = "Underwriting complete! I have your loan decision ready."
        
        next_state = state_machine.get_next_state(
            session.current_state,
            "underwriting_completed",
            {}
        )
        if next_state:
            session.transition_state(next_state)
        
        return {
            "response": response,
            "state_changed": True,
            "new_state": session.current_state.value,
            "slots_updated": {"underwriting_result": underwriting_result}
        }


underwriting_worker = UnderwritingWorker()
