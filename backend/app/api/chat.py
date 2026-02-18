from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

from app.core.session import get_session_state, ChatMessage
from app.core.intent import is_faq_intent
from app.core.rag import answer_from_policy_docs
from app.graph.loan_graph import run_stage

from app.tools.document_ocr.ocr_engine import extract_text
from app.tools.document_ocr.parsers import parse_salary_slip, parse_id_card
from app.tools.document_ocr.uploader import save_temp_file

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str


@router.post("/chat")
def chat(req: ChatRequest):
    session_id = req.session_id or "default"
    state = get_session_state(session_id)

    # --- Knowledge branch (RAG) ---
    if is_faq_intent(req.message):
        answer, _snippets = answer_from_policy_docs(req.message)
        lines = [l.strip() for l in answer.split("\n") if l.strip()]
        short_answer = "\n".join(lines[:5]) or "Please refer to the loan policy."
        return {
            "session_id": session_id,
            "reply": short_answer,
            "stage": state.stage,
            "done": False
        }

    # --- Store user message ---
    state.messages.append(
        ChatMessage(role="user", type="chat", content=req.message)
    )

    # --- Dialogue Manager / State Machine ---
    result = run_stage(state, req.message)

    # Defensive guard
    if result is None:
        return {
            "reply": "Something went wrong. Please try again.",
            "stage": state.stage,
            "done": False
        }

    state.stage = result["next_stage"]
    for k, v in result["updates"].items():
        setattr(state, k, v)

    state.messages.append(
        ChatMessage(role="system", type="chat", content=result["message"])
    )

    done = state.stage in ["COMPLETED", "ESCALATED"]

    return {
        "session_id": session_id,
        "reply": result["message"],
        "stage": state.stage,
        "done": done
    }


# Backward/alternate route aliases (some clients may still call these)
@router.post("/api/chat/message")
def chat_message(req: ChatRequest):
    return chat(req)


@router.post("/api/v1/chat")
def chat_v1(req: ChatRequest):
    return chat(req)


@router.post("/upload-doc")
def upload_doc(
    session_id: str,
    doc_type: str,
    file: UploadFile = File(...)
):
    try:
        path = save_temp_file(file, session_id)
        text = extract_text(path)

        if doc_type == "salary_slip":
            data, confidence = parse_salary_slip(text)
        elif doc_type == "id_card":
            data, confidence = parse_id_card(text)
        else:
            raise HTTPException(status_code=400, detail="Invalid doc_type")

        if confidence < 0.6:
            return {
                "status": "LOW_CONFIDENCE",
                "confidence": confidence,
                "extracted": data,
                "message": "Document unclear. Please re-upload."
            }

        return {
            "status": "OK",
            "confidence": confidence,
            "extracted": data
        }

    except Exception as e:
        return {
            "status": "FAILED",
            "error": str(e)
        }
