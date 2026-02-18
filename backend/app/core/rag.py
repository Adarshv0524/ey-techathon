# app/core/rag.py

from typing import List, Tuple
import os
import re

# In-memory cache
_POLICY_DOCS: List[str] = []


def load_policy_docs() -> List[str]:
    """
    Load policy documents from local text files.
    MVP: simple flat text loader.
    """
    docs = []

    policy_dir = os.path.join(os.path.dirname(__file__), "..", "policy_docs")
    policy_dir = os.path.abspath(policy_dir)

    if not os.path.isdir(policy_dir):
        return docs

    for fname in os.listdir(policy_dir):
        if fname.endswith(".txt"):
            with open(os.path.join(policy_dir, fname), "r", encoding="utf-8") as f:
                docs.append(f.read().strip())

    return docs


def _ensure_loaded() -> None:
    global _POLICY_DOCS
    if not _POLICY_DOCS:
        _POLICY_DOCS = load_policy_docs()


def retrieve_relevant_snippets(
    question: str,
    docs: List[str],
    top_k: int = 3,
) -> List[str]:
    """
    Very simple keyword-based retrieval (MVP-safe).
    No embeddings yet.
    """
    q = question.lower()
    scored = []

    for doc in docs:
        score = 0
        for word in re.findall(r"\w+", q):
            if word in doc.lower():
                score += 1
        if score > 0:
            scored.append((score, doc))

    scored.sort(reverse=True, key=lambda x: x[0])
    return [doc for _, doc in scored[:top_k]]


def answer_from_policy_docs(question: str) -> Tuple[str, List[str]]:
    """
    Deterministic RAG answer.
    Returns (answer, snippets).
    """
    _ensure_loaded()

    if not _POLICY_DOCS:
        return "No policy documents are configured yet.", []

    snippets = retrieve_relevant_snippets(question, _POLICY_DOCS, top_k=3)

    # Fallback: return first doc if nothing matches
    if not snippets:
        snippets = _POLICY_DOCS[:1]

    if not snippets:
        return "I could not find relevant policy information.", []

    # MVP rule: answer is first snippet verbatim
    return snippets[0], snippets
