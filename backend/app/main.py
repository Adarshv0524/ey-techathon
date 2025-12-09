# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="TIA-Sales Chat Backend - Phase 1",
    version="0.2.0",
)

# Allow frontend (file:// or http://localhost) to hit this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for dev/hackathon; later you can restrict
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str | None = None


@app.get("/health")
def health_check():
    """
    Simple health endpoint for Postman/monitoring.
    """
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(payload: ChatRequest):
    """
    Phase 1: minimal echo-style chatbot.

    - Takes a message and optional session_id.
    - Returns a simple echo response.
    """
    # For now, no state or AI: just echo back.
    reply_text = f"You said: {payload.message}"

    return ChatResponse(
        reply=reply_text,
        session_id=payload.session_id,
    )
