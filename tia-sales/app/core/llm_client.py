import httpx
import json
import logging
from typing import Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)


class HuggingFaceLLMClient:
    """Centralized HuggingFace LLM API client with structured output support"""
    
    def __init__(self):
        self.api_key = settings.HF_API_KEY
        self.base_url = settings.HF_API_URL
        self.timeout = settings.HF_TIMEOUT
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def generate_structured(
        self,
        prompt: str,
        model: str,
        json_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.1,
        max_tokens: int = 512
    ) -> Dict[str, Any]:
        """
        Generate structured JSON output from LLM
        
        Args:
            prompt: The instruction prompt
            model: HuggingFace model identifier
            json_schema: Expected JSON schema for structured output
            temperature: Sampling temperature (lower = more deterministic)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Parsed JSON response
        """
        try:
            payload = {
                "inputs": prompt,
                "parameters": {
                    "temperature": temperature,
                    "max_new_tokens": max_tokens,
                    "return_full_text": False,
                    "do_sample": temperature > 0
                }
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/{model}",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                
                if isinstance(result, list) and len(result) > 0:
                    generated_text = result[0].get("generated_text", "")
                else:
                    generated_text = result.get("generated_text", "")
                
                # Extract JSON from response
                parsed_json = self._extract_json(generated_text)
                
                # Validate against schema if provided
                if json_schema and parsed_json:
                    self._validate_schema(parsed_json, json_schema)
                
                return parsed_json
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error calling HuggingFace API: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {e}")
            return {"error": "Failed to parse structured output"}
        except Exception as e:
            logger.error(f"Unexpected error in LLM call: {e}")
            raise
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON object from text response"""
        text = text.strip()
        
        # Try to find JSON block
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        
        if json_start != -1 and json_end > json_start:
            json_text = text[json_start:json_end]
            try:
                return json.loads(json_text)
            except json.JSONDecodeError:
                pass
        
        # Try parsing entire text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning(f"Could not extract JSON from: {text[:100]}")
            return {}
    
    def _validate_schema(self, data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """Basic schema validation"""
        required_fields = schema.get("required", [])
        properties = schema.get("properties", {})
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        for field, value in data.items():
            if field in properties:
                expected_type = properties[field].get("type")
                if expected_type == "string" and not isinstance(value, str):
                    raise ValueError(f"Field {field} should be string")
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    raise ValueError(f"Field {field} should be number")
                elif expected_type == "boolean" and not isinstance(value, bool):
                    raise ValueError(f"Field {field} should be boolean")
        
        return True
    
    async def classify(self, text: str, categories: list[str]) -> str:
        """Classify text into one of the provided categories"""
        prompt = f"""Classify the following user message into exactly ONE category.

Categories: {', '.join(categories)}

User message: "{text}"

Respond with ONLY a JSON object in this format:
{{"category": "CATEGORY_NAME"}}

JSON:"""
        
        schema = {
            "type": "object",
            "properties": {
                "category": {"type": "string"}
            },
            "required": ["category"]
        }
        
        result = await self.generate_structured(
            prompt=prompt,
            model=settings.HF_MODEL_CLASSIFICATION,
            json_schema=schema,
            temperature=0.1
        )
        
        category = result.get("category", "OUT_OF_SCOPE")
        if category not in categories:
            category = "OUT_OF_SCOPE"
        
        return category
    
    async def extract_slot(self, text: str, slot_name: str, slot_description: str) -> Dict[str, Any]:
        """Extract specific slot value from user message"""
        prompt = f"""Extract the {slot_name} from the user's message.

{slot_description}

User message: "{text}"

Respond with ONLY a JSON object in this format:
{{"value": "extracted_value", "confidence": 0.0-1.0}}

If not found, set value to null and confidence to 0.0.

JSON:"""
        
        schema = {
            "type": "object",
            "properties": {
                "value": {"type": ["string", "number", "boolean", "null"]},
                "confidence": {"type": "number"}
            },
            "required": ["value", "confidence"]
        }
        
        result = await self.generate_structured(
            prompt=prompt,
            model=settings.HF_MODEL_EXTRACTION,
            json_schema=schema,
            temperature=0.1
        )
        
        return result
    
    async def rephrase(self, content: str, tone: str = "professional") -> str:
        """Rephrase content in natural language"""
        prompt = f"""Rephrase the following content in a {tone} and conversational tone.

Content: {content}

Rephrased response:"""
        
        result = await self.generate_structured(
            prompt=prompt,
            model=settings.HF_MODEL_GENERATION,
            temperature=0.3,
            max_tokens=256
        )
        
        # For rephrasing, we accept plain text or extract 'response' field
        if isinstance(result, dict) and "response" in result:
            return result["response"]
        elif isinstance(result, dict):
            return content  # Fallback
        else:
            return str(result)


# Global LLM client instance
llm_client = HuggingFaceLLMClient()
