import logging
from typing import Dict, Any
from app.core.llm_client import llm_client
from app.guardrails.output_guardrail import output_guardrail

logger = logging.getLogger(__name__)


class ResponseSynthesizer:
    """Converts structured results to natural language responses"""
    
    async def synthesize(self, structured_data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Convert structured data to natural language
        
        Args:
            structured_data: Worker output or structured result
            context: Session context (state, slots, etc.)
            
        Returns:
            Natural language response
        """
        # If response is already provided, rephrase for variety
        if "response" in structured_data:
            base_response = structured_data["response"]
            
            # Check if rephrasing is needed (avoid repetition)
            if self._should_rephrase(base_response, context):
                try:
                    rephrased = await llm_client.rephrase(base_response, tone="professional")
                    response = rephrased if rephrased else base_response
                except Exception as e:
                    logger.error(f"Error rephrasing response: {e}")
                    response = base_response
            else:
                response = base_response
        else:
            # Generate response from structured data
            response = self._generate_from_structured(structured_data, context)
        
        # Apply output guardrails
        validated_response = output_guardrail.validate(
            response,
            context={"in_loan_flow": context.get("state") not in ["GREETING", "COMPLETED"]}
        )
        
        return validated_response
    
    def _should_rephrase(self, response: str, context: Dict[str, Any]) -> bool:
        """Determine if response should be rephrased"""
        # Check history for repetition
        history = context.get("history", [])
        recent_responses = [msg["content"] for msg in history[-3:] if msg.get("role") == "assistant"]
        
        # If similar response in recent history, rephrase
        for prev_response in recent_responses:
            if self._similarity(response, prev_response) > 0.7:
                return True
        
        return False
    
    def _similarity(self, text1: str, text2: str) -> float:
        """Simple similarity check"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _generate_from_structured(self, data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Generate response from structured data when no response field exists"""
        # Default fallback
        state = context.get("state", "UNKNOWN")
        
        if "error" in data:
            return f"I encountered an issue: {data['error']}. Could you please try again?"
        
        if state == "DECISION":
            decision = data.get("decision")
            if decision == "APPROVED":
                return "Congratulations! Your loan application has been approved."
            elif decision == "REJECTED":
                return "I'm sorry, but your loan application was not approved at this time."
            else:
                return "Your application is under review."
        
        return "Thank you for the information. Let's continue with your application."


response_synthesizer = ResponseSynthesizer()
