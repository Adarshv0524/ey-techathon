import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.tools.rag.rag_engine import rag_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/faq", tags=["faq"])


class FAQRequest(BaseModel):
    question: str


class FAQResponse(BaseModel):
    answer: str
    sources: list
    confidence: float


@router.post("/ask", response_model=FAQResponse)
async def ask_question(request: FAQRequest):
    """
    Standalone FAQ endpoint using RAG
    
    Answers loan policy questions without session context
    """
    try:
        result = await rag_engine.query(request.question, top_k=3)
        
        return FAQResponse(
            answer=result["answer"],
            sources=result["sources"],
            confidence=result["confidence"]
        )
    
    except Exception as e:
        logger.error(f"Error in FAQ query: {e}")
        raise HTTPException(status_code=500, detail="Failed to process question")
