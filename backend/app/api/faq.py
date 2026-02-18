# app/api/faq.py

from fastapi import APIRouter
from pydantic import BaseModel
from app.core.rag import answer_from_policy_docs

router = APIRouter()


class FaqRequest(BaseModel):
    question: str


class FaqResponse(BaseModel):
    answer: str
    snippets: list[str]


@router.post("/faq/query", response_model=FaqResponse)
def faq(payload: FaqRequest):
    answer, snippets = answer_from_policy_docs(payload.question)
    return FaqResponse(answer=answer, snippets=snippets)
