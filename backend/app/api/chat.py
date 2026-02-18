import logging
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Optional
from app.core.session import session_manager
from app.guardrails.input_guardrail import input_guardrail
from app.graph.router import semantic_router, IntentType
from app.graph.dialogue_manager import dialogue_manager
from app.graph.response_synthesizer import response_synthesizer
from app.tools.rag.rag_engine import rag_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str


class ChatResponse(BaseModel):
    session_id: str
    response: str
    current_state: str
    slots: dict


@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest = Body(...)):
    """
    Main conversational endpoint
    
    Processes user message through:
    1. Input guardrails
    2. Semantic router
    3. Context manager
    4. Dialogue manager OR RAG engine
    5. Response synthesizer
    6. Output guardrails
    """
    try:
        # Validate input
        is_valid, result = input_guardrail.validate(request.message)
        if not is_valid:
            raise HTTPException(status_code=400, detail=result)
        
        sanitized_message = result
        
        # Get or create session
        if request.session_id:
            session = await session_manager.get_session(request.session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found or expired")
        else:
            session = await session_manager.create_session()
        
        # Add user message to history
        session.add_message("user", sanitized_message)
        
        # Route message
        intent = await semantic_router.route(sanitized_message, session.current_state.value)
        logger.info(f"Intent: {intent}")
        
        # Handle based on intent
        if intent == IntentType.GREETING:
            # Handle greeting
            if session.current_state.value == "GREETING":
                structured_result = await dialogue_manager.process_task_action(
                    sanitized_message,
                    session
                )
            else:
                structured_result = {
                    "response": "Hello! How can I help you with your loan application?",
                    "state_changed": False,
                    "new_state": session.current_state.value,
                    "slots_updated": {}
                }
        
        elif intent == IntentType.KNOWLEDGE_QUERY:
            # Handle knowledge query via RAG
            rag_result = await rag_engine.query(sanitized_message)
            structured_result = {
                "response": rag_result["answer"],
                "state_changed": False,
                "new_state": session.current_state.value,
                "slots_updated": {}
            }
        
        elif intent == IntentType.TASK_ACTION:
            # Handle task-oriented action
            structured_result = await dialogue_manager.process_task_action(
                sanitized_message,
                session
            )
        
        else:  # OUT_OF_SCOPE
            structured_result = {
                "response": "I'm specialized in helping with personal loan applications. Please ask questions related to loans, or let's continue with your application.",
                "state_changed": False,
                "new_state": session.current_state.value,
                "slots_updated": {}
            }
        
        # Synthesize response
        final_response = await response_synthesizer.synthesize(
            structured_result,
            context={
                "state": session.current_state.value,
                "history": session.history,
                "slots": session.slots
            }
        )
        
        # Add assistant response to history
        session.add_message("assistant", final_response)
        
        # Update session
        await session_manager.update_session(session)
        
        return ChatResponse(
            session_id=session.session_id,
            response=final_response,
            current_state=session.current_state.value,
            slots=session.slots
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/new-session")
async def create_new_session():
    """Create a new conversation session"""
    session = await session_manager.create_session()
    return {"session_id": session.session_id}


@router.get("/session/{session_id}")
async def get_session_info(session_id: str):
    """Retrieve session information"""
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session.to_dict()
