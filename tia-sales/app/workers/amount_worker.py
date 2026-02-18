import logging
from typing import Dict, Any
from app.core.session import SessionData
from app.graph.slot_filler import slot_filler
from app.graph.state_machine import state_machine
from app.config import settings

logger = logging.getLogger(__name__)


class AmountWorker:
    """Handles loan amount collection and validation"""
    
    async def process(self, user_message: str, session: SessionData) -> Dict[str, Any]:
        """Process loan amount input"""
        
        # Extract loan amount
        loan_amount = await slot_filler.extract_loan_amount(user_message)
        
        if loan_amount:
            session.update_slot("loan_amount", loan_amount)
            
            # Format amount for display
            formatted_amount = self._format_amount(loan_amount)
            
            response = f"Perfect! You're applying for ₹{formatted_amount}. To process your loan, I'll need some documents from you. These include your salary slip, PAN card, and Aadhaar card. Are you ready to upload them?"
            
            next_state = state_machine.get_next_state(
                session.current_state,
                "amount_provided",
                {}
            )
            if next_state:
                session.transition_state(next_state)
            
            return {
                "response": response,
                "state_changed": True,
                "new_state": session.current_state.value,
                "slots_updated": {"loan_amount": loan_amount}
            }
        
        else:
            min_amount = self._format_amount(settings.MIN_LOAN_AMOUNT)
            max_amount = self._format_amount(settings.MAX_LOAN_AMOUNT)

            raw_amount = self._extract_raw_amount(user_message)
            if raw_amount is not None:
                if raw_amount < settings.MIN_LOAN_AMOUNT:
                    response = (
                        f"The minimum loan amount is ₹{min_amount}. "
                        f"Please enter an amount between ₹{min_amount} and ₹{max_amount}."
                    )
                elif raw_amount > settings.MAX_LOAN_AMOUNT:
                    response = (
                        f"The maximum loan amount is ₹{max_amount}. "
                        f"Please enter an amount between ₹{min_amount} and ₹{max_amount}."
                    )
                else:
                    response = (
                        f"I couldn't confirm the loan amount. "
                        f"Please specify an amount between ₹{min_amount} and ₹{max_amount}."
                    )
            else:
                response = (
                    f"I couldn't determine the loan amount from your message. "
                    f"Please specify an amount between ₹{min_amount} and ₹{max_amount}."
                )

            return {
                "response": response,
                "state_changed": False,
                "new_state": session.current_state.value,
                "slots_updated": {}
            }
    
    def _format_amount(self, amount: float) -> str:
        """Format amount with commas (Indian numbering)"""
        amount_str = f"{amount:,.0f}"
        # Convert to Indian numbering system
        if amount >= 100000:
            lakhs = amount / 100000
            return f"{lakhs:,.2f} lakhs"
        return amount_str

    def _extract_raw_amount(self, user_message: str) -> float | None:
        """Extract a numeric amount from text without range validation."""
        import re

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
                    if 'lakh' in user_message.lower() or 'lac' in user_message.lower():
                        amount = amount * 100000
                    return amount
                except ValueError:
                    return None

        return None


amount_worker = AmountWorker()
