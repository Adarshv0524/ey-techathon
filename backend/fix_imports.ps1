# fix_imports.ps1
Write-Host "Fixing import errors..." -ForegroundColor Green

# Fix output_guardrail.py
$outputGuardrailContent = @'
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class OutputGuardrail:
    """Output validation and safety checks"""
    
    def validate(self, response: str, context: Optional[Dict] = None) -> str:
        """
        Validate and potentially modify output response
        
        Args:
            response: Generated response text
            context: Additional context for validation
            
        Returns:
            Validated response
        """
        if not response or not response.strip():
            return "I apologize, but I couldn't generate a proper response. Could you please rephrase your question?"
        
        # Ensure relevance
        if self._is_off_topic(response, context):
            logger.warning("Off-topic response detected")
            return "I'm here to help with your personal loan application. Could you please ask a loan-related question?"
        
        # Ensure politeness
        response = self._ensure_politeness(response)
        
        # Remove potential hallucinations
        response = self._remove_hallucinations(response)
        
        return response.strip()
    
    def _is_off_topic(self, response: str, context: Optional[Dict]) -> bool:
        """Check if response is off-topic"""
        # Check for loan-related keywords
        loan_keywords = ["loan", "amount", "interest", "document", "approval", "credit", "customer"]
        response_lower = response.lower()
        
        # If context indicates we're in a loan flow, response should be relevant
        if context and context.get("in_loan_flow"):
            has_keyword = any(keyword in response_lower for keyword in loan_keywords)
            if not has_keyword and len(response) > 50:
                return True
        
        return False
    
    def _ensure_politeness(self, response: str) -> str:
        """Ensure response maintains professional tone"""
        # Replace harsh phrases
        replacements = {
            "you must": "please",
            "you should": "I recommend you",
            "wrong": "incorrect",
            "bad": "not optimal"
        }
        
        response_lower = response.lower()
        for harsh, polite in replacements.items():
            if harsh in response_lower:
                response = response.replace(harsh, polite)
        
        return response
    
    def _remove_hallucinations(self, response: str) -> str:
        """Remove potential hallucinated content"""
        # Remove claims about capabilities we don't have
        hallucination_phrases = [
            "I can see your screen",
            "I have access to your account",
            "I checked your credit score",
            "I approved your loan"
        ]
        
        for phrase in hallucination_phrases:
            if phrase.lower() in response.lower():
                logger.warning(f"Potential hallucination detected: {phrase}")
                response = response.replace(phrase, "I can help you with")
        
        return response


output_guardrail = OutputGuardrail()
'@

$outputGuardrailContent | Out-File -FilePath "app\guardrails\output_guardrail.py" -Encoding UTF8

# Create all __init__.py files
$initFiles = @(
    "app\__init__.py",
    "app\api\__init__.py",
    "app\core\__init__.py",
    "app\graph\__init__.py",
    "app\guardrails\__init__.py",
    "app\tools\__init__.py",
    "app\tools\document_ocr\__init__.py",
    "app\tools\rag\__init__.py",
    "app\workers\__init__.py"
)

foreach ($file in $initFiles) {
    if (-not (Test-Path $file)) {
        New-Item -ItemType File -Path $file -Force | Out-Null
        Write-Host "Created: $file" -ForegroundColor Yellow
    }
}

Write-Host "`nAll fixes applied successfully!" -ForegroundColor Green
Write-Host "Now run: python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor Cyan
