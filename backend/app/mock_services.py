import logging
import asyncio
from typing import Dict, Any
import random

logger = logging.getLogger(__name__)


class MockCustomerService:
    """Mock customer validation service"""
    
    async def validate_customer_id(self, customer_id: str) -> bool:
        """Validate if customer ID exists"""
        await asyncio.sleep(0.1)  # Simulate API call
        
        # For demo, accept any CUST ID with digits
        if customer_id.startswith("CUST") and len(customer_id) > 8:
            logger.info(f"Customer ID {customer_id} validated")
            return True
        
        logger.warning(f"Customer ID {customer_id} invalid")
        return False


class MockUnderwritingService:
    """Mock underwriting/credit assessment service"""
    
    async def assess_loan(
        self,
        customer_id: str,
        loan_amount: float,
        income_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate loan underwriting"""
        await asyncio.sleep(1)  # Simulate processing time
        
        # Extract income
        monthly_salary = float(income_data.get("monthly_salary", 50000))
        
        # Simple underwriting logic
        max_eligible = monthly_salary * 24  # 2 years of salary
        
        if loan_amount > max_eligible:
            decision = "REJECTED"
            reason = f"Requested amount exceeds eligible limit (₹{max_eligible:,.0f})"
            approved_amount = 0
            interest_rate = 0
        
        elif monthly_salary < 25000:
            decision = "REJECTED"
            reason = "Minimum income requirement not met (₹25,000/month)"
            approved_amount = 0
            interest_rate = 0
        
        else:
            # Approve with varying interest rates
            decision = "APPROVED"
            reason = "All eligibility criteria met"
            approved_amount = loan_amount
            
            # Interest rate based on amount
            if loan_amount < 200000:
                interest_rate = 12.5
            elif loan_amount < 500000:
                interest_rate = 11.5
            else:
                interest_rate = 10.5
        
        result = {
            "decision": decision,
            "reason": reason,
            "approved_amount": approved_amount,
            "interest_rate": interest_rate,
            "customer_id": customer_id
        }
        
        logger.info(f"Underwriting result: {result}")
        return result


# Global instances
mock_customer_service = MockCustomerService()
mock_underwriting_service = MockUnderwritingService()
