import logging
from enum import Enum
from app.core.llm_client import llm_client

logger = logging.getLogger(__name__)


class IntentType(str, Enum):
    """User intent classification"""
    GREETING = "GREETING"
    KNOWLEDGE_QUERY = "KNOWLEDGE_QUERY"
    TASK_ACTION = "TASK_ACTION"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


class SemanticRouter:
    """Routes user messages to appropriate handlers based on intent"""
    
    async def route(self, user_message: str, session_state: str) -> IntentType:
        """
        Classify user intent using LLM
        
        Args:
            user_message: User's input text
            session_state: Current conversation state
            
        Returns:
            Classified intent type
        """
        # Quick pattern matching for common cases
        quick_intent = self._quick_classify(user_message, session_state)
        if quick_intent:
            return quick_intent
        
        # Use LLM for ambiguous cases
        categories = [e.value for e in IntentType]
        
        try:
            intent = await llm_client.classify(user_message, categories)
            logger.info(f"Routed message to intent: {intent}")
            return IntentType(intent)
        except Exception as e:
            logger.error(f"Error in semantic routing: {e}")
            return IntentType.TASK_ACTION  # Default to task action
    
    def _quick_classify(self, message: str, state: str) -> IntentType:
        """Quick pattern-based classification"""
        message_lower = message.lower().strip()
        
        # Greetings
        greeting_patterns = ["hello", "hi", "hey", "good morning", "good afternoon", "namaste"]
        if any(pattern in message_lower for pattern in greeting_patterns) and len(message) < 50:
            return IntentType.GREETING
        
        # Knowledge queries
        knowledge_patterns = ["what is", "how does", "can you explain", "tell me about", "interest rate", "eligibility", "documents required"]
        if any(pattern in message_lower for pattern in knowledge_patterns):
            return IntentType.KNOWLEDGE_QUERY
        
        # Out of scope
        out_of_scope_patterns = ["weather", "joke", "movie", "recipe", "sports", "politics"]
        if any(pattern in message_lower for pattern in out_of_scope_patterns):
            return IntentType.OUT_OF_SCOPE
        
        # Default to task action if in active flow
        if state not in ["GREETING", "COMPLETED"]:
            return IntentType.TASK_ACTION
        
        return None


semantic_router = SemanticRouter()
