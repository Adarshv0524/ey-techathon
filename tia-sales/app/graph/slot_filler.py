import logging
import re
from typing import Dict, Any, Optional
from app.core.llm_client import llm_client
from app.config import settings

logger = logging.getLogger(__name__)


class SlotFiller:
    """Extracts and validates structured data from user messages"""
    
    async def extract_consent(self, user_message: str) -> Optional[bool]:
        """Extract consent (yes/no) from user message"""
        message_lower = user_message.lower().strip()
        
        # Pattern matching for clear responses
        yes_patterns = ["yes", "yeah", "yep", "sure", "ok", "okay", "i agree", "i consent", "proceed"]
        no_patterns = ["no", "nope", "nah", "don't", "do not", "disagree", "decline"]
        
        if any(pattern in message_lower for pattern in yes_patterns):
            return True
        elif any(pattern in message_lower for pattern in no_patterns):
            return False
        
        # Use LLM for ambiguous cases
        try:
            result = await llm_client.extract_slot(
                text=user_message,
                slot_name="consent",
                slot_description="Extract whether user agrees/consents (true) or disagrees (false)."
            )
            
            value = result.get("value")
            confidence = result.get("confidence", 0.0)
            
            if confidence > 0.7 and isinstance(value, bool):
                return value
        except Exception as e:
            logger.error(f"Error extracting consent: {e}")
        
        return None
    
    async def extract_customer_id(self, user_message: str) -> Optional[str]:
        """Extract customer ID from user message"""
        # Pattern: CUST followed by 6-10 digits
        pattern = r'\b(CUST\d{6,10}|\d{6,10})\b'
        match = re.search(pattern, user_message, re.IGNORECASE)
        
        if match:
            customer_id = match.group(1).upper()
            if not customer_id.startswith("CUST"):
                customer_id = f"CUST{customer_id}"
            return customer_id
        
        # Use LLM for extraction
        try:
            result = await llm_client.extract_slot(
                text=user_message,
                slot_name="customer_id",
                slot_description="Extract customer ID (format: CUST followed by digits, or just digits)."
            )
            
            value = result.get("value")
            confidence = result.get("confidence", 0.0)
            
            if confidence > 0.6 and value:
                customer_id = str(value).upper()
                if not customer_id.startswith("CUST") and customer_id.isdigit():
                    customer_id = f"CUST{customer_id}"
                return customer_id
        except Exception as e:
            logger.error(f"Error extracting customer_id: {e}")
        
        return None
    
    async def extract_loan_amount(self, user_message: str) -> Optional[float]:
        """Extract loan amount from user message"""
        # Pattern for amounts with various formats
        patterns = [
            r'₹\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:lakh|lac|l)?',
            r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:lakh|lac|l)',
            r'₹\s*(\d+(?:,\d+)*(?:\.\d+)?)',
            r'(\d+(?:,\d+)*(?:\.\d+)?)\s*rupees',
            r'\b(\d{2,7})\s*(k|thousand)\b',
            r'\b(\d{4,7})\b'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_message, re.IGNORECASE)
            if match:
                if match.lastindex and match.lastindex >= 2 and match.group(2):
                    multiplier = 1000
                else:
                    multiplier = 1

                amount_str = match.group(1).replace(',', '')
                try:
                    amount = float(amount_str) * multiplier
                    
                    # Check if it's in lakhs
                    if 'lakh' in user_message.lower() or 'lac' in user_message.lower():
                        amount = amount * 100000
                    
                    # Validate range
                    if settings.MIN_LOAN_AMOUNT <= amount <= settings.MAX_LOAN_AMOUNT:
                        return amount
                except ValueError:
                    pass
        
        # Use LLM for extraction
        try:
            result = await llm_client.extract_slot(
                text=user_message,
                slot_name="loan_amount",
                slot_description=f"Extract loan amount in rupees (numeric value). Convert lakhs to rupees. Range: {settings.MIN_LOAN_AMOUNT} to {settings.MAX_LOAN_AMOUNT}."
            )
            
            value = result.get("value")
            confidence = result.get("confidence", 0.0)
            
            if confidence > 0.6 and value:
                try:
                    amount = float(value)
                    if settings.MIN_LOAN_AMOUNT <= amount <= settings.MAX_LOAN_AMOUNT:
                        return amount
                except (ValueError, TypeError):
                    pass
        except Exception as e:
            logger.error(f"Error extracting loan_amount: {e}")
        
        return None
    
    async def detect_correction(self, user_message: str) -> Optional[str]:
        """Detect if user wants to correct previous information"""
        correction_patterns = [
            "actually", "wait", "no", "correction", "change", "wrong",
            "meant to say", "i mean", "not", "instead"
        ]
        
        message_lower = user_message.lower()
        if any(pattern in message_lower for pattern in correction_patterns):
            return "CORRECTION_DETECTED"
        
        return None


slot_filler = SlotFiller()
