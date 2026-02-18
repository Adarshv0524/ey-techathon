import re
import logging
from typing import Tuple
from app.config import settings

logger = logging.getLogger(__name__)


class InputGuardrail:
    """Input validation and sanitization"""
    
    def __init__(self):
        self.max_length = settings.INPUT_MAX_LENGTH
        self.offensive_keywords = settings.OFFENSIVE_KEYWORDS
    
    def validate(self, user_input: str) -> Tuple[bool, str]:
        """
        Validate user input
        
        Returns:
            (is_valid, sanitized_input or error_message)
        """
        if not user_input or not user_input.strip():
            return False, "Empty input"
        
        # Length check
        if len(user_input) > self.max_length:
            return False, f"Input too long (max {self.max_length} characters)"
        
        # Check for injection attempts
        if self._contains_injection_patterns(user_input):
            logger.warning(f"Potential injection attempt detected: {user_input[:50]}")
            return False, "Invalid input detected"
        
        # Check offensive keywords
        if self._contains_offensive_content(user_input):
            logger.warning(f"Offensive content detected: {user_input[:50]}")
            return False, "Please keep the conversation professional"
        
        # Sanitize
        sanitized = self._sanitize(user_input)
        
        return True, sanitized
    
    def _contains_injection_patterns(self, text: str) -> bool:
        """Check for common injection patterns"""
        patterns = [
            r"<script",
            r"javascript:",
            r"onerror=",
            r"onclick=",
            r"\bUNION\b.*\bSELECT\b",
            r"\bDROP\b.*\bTABLE\b",
            r"--.*$",
            r"/\*.*\*/"
        ]
        
        text_lower = text.lower()
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        return False
    
    def _contains_offensive_content(self, text: str) -> bool:
        """Check for offensive keywords"""
        text_lower = text.lower()
        for keyword in self.offensive_keywords:
            if keyword.lower() in text_lower:
                return True
        return False
    
    def _sanitize(self, text: str) -> str:
        """Sanitize input text"""
        # Remove excessive whitespace
        text = " ".join(text.split())
        
        # Remove control characters
        text = "".join(char for char in text if ord(char) >= 32 or char in "\n\t")
        
        return text.strip()


input_guardrail = InputGuardrail()
