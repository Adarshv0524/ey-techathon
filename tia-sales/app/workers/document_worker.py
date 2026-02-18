import logging
from typing import Dict, Any
from app.core.session import SessionData
from app.graph.state_machine import state_machine
from app.tools.document_ocr.ocr_engine import ocr_engine
from app.core.llm_client import llm_client

logger = logging.getLogger(__name__)


class DocumentWorker:
    """Handles document upload and OCR processing"""
    
    async def process_need_docs(self, user_message: str, session: SessionData) -> Dict[str, Any]:
        """Handle document requirement acknowledgment"""
        message_lower = user_message.lower()
        affirmative = any(word in message_lower for word in ["yes", "ready", "sure", "ok", "proceed"])

        if not affirmative:
            try:
                result = await llm_client.extract_slot(
                    text=user_message,
                    slot_name="ready_to_upload",
                    slot_description="Extract whether the user is ready to upload documents (true/false)."
                )
                if result.get("confidence", 0.0) > 0.6 and result.get("value") is True:
                    affirmative = True
            except Exception as e:
                logger.error(f"Error extracting ready_to_upload: {e}")

        if affirmative:
            response = "Great! Please upload your documents. You can send them one by one or all together. I support JPG, PNG, and PDF formats."
            
            next_state = state_machine.get_next_state(
                session.current_state,
                "docs_acknowledged",
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
        else:
            response = "No problem. Take your time. Let me know when you're ready to upload your documents."
            
            return {
                "response": response,
                "state_changed": False,
                "new_state": session.current_state.value,
                "slots_updated": {}
            }
    
    async def process_upload(self, user_message: str, session: SessionData) -> Dict[str, Any]:
        """Handle document upload (simulated)"""
        documents = session.get_slot("documents") or {}
        ocr_data = session.get_slot("ocr_data") or {}

        if documents:
            response = "I've received your documents. Let me summarize what I extracted."
            response += "\n\nI've extracted the following information:\n"

            if "salary_slip" in ocr_data and ocr_data["salary_slip"].get("monthly_salary"):
                response += f"- Monthly Salary: ₹{ocr_data['salary_slip']['monthly_salary']}\n"
            if "pan_card" in ocr_data and ocr_data["pan_card"].get("pan_number"):
                response += f"- PAN Number: {ocr_data['pan_card']['pan_number']}\n"
            if "aadhaar" in ocr_data and ocr_data["aadhaar"].get("aadhaar_number"):
                response += f"- Aadhaar: {ocr_data['aadhaar']['aadhaar_number']}\n"

            response += "\nIs this information correct?"

            next_state = state_machine.get_next_state(
                session.current_state,
                "docs_uploaded",
                {}
            )
            if next_state:
                session.transition_state(next_state)

            return {
                "response": response,
                "state_changed": True,
                "new_state": session.current_state.value,
                "slots_updated": {"ocr_data": ocr_data}
            }

        message_lower = user_message.lower()
        if "uploaded" in message_lower or "sent" in message_lower or "here" in message_lower:
            response = "I didn't detect any uploaded documents yet. Please use the upload panel to send them."
            return {
                "response": response,
                "state_changed": False,
                "new_state": session.current_state.value,
                "slots_updated": {}
            }

        response = "Please upload your documents (salary slip, PAN, Aadhaar). Use the upload panel above, then tell me when you're done."

        return {
            "response": response,
            "state_changed": False,
            "new_state": session.current_state.value,
            "slots_updated": {}
        }
    
    async def process_confirm(self, user_message: str, session: SessionData) -> Dict[str, Any]:
        """Handle OCR confirmation"""
        message_lower = user_message.lower()
        confirmed = any(word in message_lower for word in ["yes", "correct", "right", "accurate"])

        if not confirmed:
            try:
                result = await llm_client.extract_slot(
                    text=user_message,
                    slot_name="ocr_confirmed",
                    slot_description="Extract whether the user confirms OCR data is correct (true/false)."
                )
                if result.get("confidence", 0.0) > 0.6 and result.get("value") is True:
                    confirmed = True
            except Exception as e:
                logger.error(f"Error extracting ocr_confirmed: {e}")
        
        if confirmed:
            response = "Perfect! I'm now processing your loan application through our underwriting system. This will take a few seconds..."
            
            next_state = state_machine.get_next_state(
                session.current_state,
                "ocr_confirmed",
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
        else:
            response = "I understand there's an issue with the extracted data. Please re-upload your documents so I can process them again."
            
            next_state = state_machine.get_next_state(
                session.current_state,
                "ocr_rejected",
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


document_worker = DocumentWorker()
