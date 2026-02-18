import logging
from typing import Dict, Any
from app.core.session import SessionData
from app.graph.state_machine import state_machine
from app.tools.pdf_generator import pdf_generator

logger = logging.getLogger(__name__)


class DecisionWorker:
    """Handles final loan decision communication with PDF generation"""
    
    async def process(self, user_message: str, session: SessionData) -> Dict[str, Any]:
        """Deliver loan decision and generate PDF document"""
        
        underwriting_result = session.get_slot("underwriting_result")
        
        if not underwriting_result:
            return {
                "response": "There was an issue retrieving your decision. Please contact support.",
                "state_changed": False,
                "new_state": session.current_state.value,
                "slots_updated": {}
            }
        
        decision = underwriting_result.get("decision")
        reason = underwriting_result.get("reason", "")
        approved_amount = underwriting_result.get("approved_amount")
        interest_rate = underwriting_result.get("interest_rate")
        
        session.update_slot("decision", decision)
        
        # Generate PDF document
        pdf_path = None
        try:
            session_dict = {
                "customer_id": session.get_slot("customer_id"),
                "loan_amount": session.get_slot("loan_amount"),
                "ocr_data": session.get_slot("ocr_data")
            }
            
            if decision == "APPROVED":
                pdf_path = pdf_generator.generate_approval_letter(
                    session_dict,
                    underwriting_result
                )
            else:
                pdf_path = pdf_generator.generate_rejection_letter(
                    session_dict,
                    underwriting_result
                )
            
            session.update_slot("decision_document", pdf_path)
            logger.info(f"Generated decision document: {pdf_path}")
        
        except Exception as e:
            logger.error(f"Failed to generate PDF document: {e}")
            pdf_path = None
        
        # Construct response
        if decision == "APPROVED":
            response = f"🎉 Congratulations! Your loan application has been APPROVED!\n\n"
            response += f"**Approved Amount:** ₹{approved_amount:,.0f}\n"
            response += f"**Interest Rate:** {interest_rate}% per annum\n"
            response += f"**Reason:** {reason}\n\n"
            
            if pdf_path:
                response += f"📄 Your official approval letter has been generated and saved at:\n`{pdf_path}`\n\n"
            
            response += "You'll receive further instructions via email and SMS. Thank you for choosing TIA Personal Loans!"
        
        elif decision == "REJECTED":
            response = f"Unfortunately, we're unable to approve your loan application at this time.\n\n"
            response += f"**Reason:** {reason}\n\n"
            
            if pdf_path:
                response += f"📄 A detailed decision letter has been generated at:\n`{pdf_path}`\n\n"
            
            response += "You may reapply after addressing the concerns mentioned. If you have questions, please contact our support team."
        
        else:
            response = f"Your application is currently under manual review.\n\n"
            response += f"**Reason:** {reason}\n\n"
            
            if pdf_path:
                response += f"📄 Status document saved at:\n`{pdf_path}`\n\n"
            
            response += "We'll get back to you within 2-3 business days. Thank you for your patience."
        
        next_state = state_machine.get_next_state(
            session.current_state,
            "decision_delivered",
            {}
        )
        if next_state:
            session.transition_state(next_state)
        
        return {
            "response": response,
            "state_changed": True,
            "new_state": session.current_state.value,
            "slots_updated": {
                "decision": decision,
                "decision_document": pdf_path
            }
        }


decision_worker = DecisionWorker()
