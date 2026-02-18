# backend/app/graph/workers.py
"""
Comprehensive worker module for TIA-Sales conversational flow.

This module contains:
- a safe wrapper around HuggingFace inference API (call_llm)
- robust deterministic fallbacks for intent detection and NLU parsing
- a Conversation Intelligence Pipeline (CIP) baked into helpers
- stateful retry and response-variation logic (humor/clarity escalation)
- pure worker functions that always return a dict with keys:
    {"next_stage": LoanStage.*, "message": "...", "updates": {...}}
- defensive guards so no worker returns None and no server crash occurs

Integration notes:
- This file expects LoanStage enum at app.core.session.LoanStage
- It expects mock services: app.mock_services.get_crm_profile, get_bureau_report
- It expects underwriting.evaluate_application
- The chat endpoint (or run_stage) should call these workers exactly as before.
"""

from typing import Any, Dict, Optional, Tuple
import os
import json
import requests
import re
import math
import time

from app.core.session import LoanStage
from app.mock_services import get_crm_profile, get_bureau_report
from app.underwriting import evaluate_application

# ---------------------------------------------------------------------------
# Configuration: Hugging Face model + timeouts
# ---------------------------------------------------------------------------
# Default to Mistral Instruct on Hugging Face Inference API.
HF_API_URL = os.getenv("HF_API_URL") or "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"

# Prefer the standard HF token name used in backend/.env.
HF_API_TOKEN = (
    os.getenv("HUGGINGFACEHUB_API_TOKEN")
    or os.getenv("HF_API_TOKEN")
    or os.getenv("HF_API_TOKEN")
)

LLM_TIMEOUT_SECONDS = 10
LLM_DEFAULT_TEMPERATURE = 0.2

# ---------------------------------------------------------------------------
# Utility: Safe call to LLM (returns string or None)
# The function expects the model to return plain text, but we will ask JSON when needed.
# Always validates JSON when expecting it.
# ---------------------------------------------------------------------------


def call_llm_raw(prompt: str, temperature: float = LLM_DEFAULT_TEMPERATURE, max_tokens: int = 128) -> Optional[str]:
    """
    Call HF inference API with basic error handling.
    Returns the string output (may be free text) or None on any failure.
    """
    if not HF_API_TOKEN:
        # If token is not present, treat as no-LLM environment.
        return None

    headers = {"Authorization": f"Bearer {HF_API_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "temperature": temperature,
            "max_new_tokens": max_tokens,
            "return_full_text": False,
        },
    }
    try:
        resp = requests.post(HF_API_URL, headers=headers, json=payload, timeout=LLM_TIMEOUT_SECONDS)
        resp.raise_for_status()
        data = resp.json()
        # Many inference endpoints return a list; handle both
        if isinstance(data, list) and len(data) > 0:
            out = data[0].get("generated_text") or data[0].get("text") or ""
        elif isinstance(data, dict) and "generated_text" in data:
            out = data["generated_text"]
        else:
            # Fallback: stringify
            out = json.dumps(data)
        return out.strip()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Helper: try to call LLM for strict JSON extraction and parse result safely
# ---------------------------------------------------------------------------


def call_llm_json(prompt: str, temperature: float = 0.0, max_tokens: int = 128) -> Optional[Dict[str, Any]]:
    """
    Calls LLM and expects a JSON object in output. If parsing fails, returns None.
    Use this for structured extraction only.
    """
    out = call_llm_raw(prompt, temperature=temperature, max_tokens=max_tokens)
    if not out:
        return None
    # Try to find first JSON object in the output text
    first_brace = out.find("{")
    first_bracket = out.find("[")
    start = -1
    if first_brace != -1:
        start = first_brace
    elif first_bracket != -1:
        start = first_bracket
    if start == -1:
        return None
    candidate = out[start:]
    # strip trailing punctuation
    # Attempt to load progressively shorter suffix until it is valid JSON
    for end in range(len(candidate), 0, -1):
        try:
            obj = json.loads(candidate[:end])
            return obj
        except Exception:
            continue
    # If not JSON, return None
    return None


# ---------------------------------------------------------------------------
# Deterministic numeric word parsing utility (fallback, covers lakh/crore/units)
# We support:
# - "4 lakh", "4.5 lakh", ".9 million", "hundred thousand", "100k", "1m", "43 crore", "4 million billion" (invalid)
# ---------------------------------------------------------------------------

# word -> multiplier
_WORD_UNITS = {
    "thousand": 1_000,
    "k": 1_000,
    "k.": 1_000,
    "lakh": 100_000,
    "lakhs": 100_000,
    "lacs": 100_000,
    "lac": 100_000,
    "million": 1_000_000,
    "m": 1_000_000,
    "billion": 1_000_000_000,
    "crore": 10_000_000,
    "cr": 10_000_000,
}

_NUMBER_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
    "hundred": 100,
    "thousand": 1000,
    "lakh": 100000,
}


def words_to_number(text: str) -> Optional[float]:
    """
    Simplified mapping for common patterns like 'one hundred twenty thousand', 'one lakh', 'two million'.
    This is a fallback and intentionally conservative.
    """
    t = text.lower().replace(",", "").strip()
    # direct integer
    if re.fullmatch(r"\d+", t):
        try:
            return float(int(t))
        except Exception:
            return None
    # decimal pattern like .9 million
    m = re.match(r"^\.(\d+)\s*(\w+)", t)
    if m:
        frac = float("0." + m.group(1))
        unit = m.group(2)
        if unit in _WORD_UNITS:
            return frac * _WORD_UNITS[unit]
    # simple "100k", "1m", "43cr", "43 crore"
    m2 = re.match(r"^([\d\.]+)\s*([a-zA-Z]+)$", t)
    if m2:
        try:
            num = float(m2.group(1))
        except Exception:
            return None
        unit = m2.group(2).lower()
        if unit in _WORD_UNITS:
            return num * _WORD_UNITS[unit]
        # support 'k' 'm' suffix
        if unit.endswith("k"):
            return num * 1_000
        if unit.endswith("m"):
            return num * 1_000_000
        if unit.endswith("cr") or "crore" in unit:
            return num * 10_000_000
    # textual numbers e.g., "hundred thousand", "one lakh"
    tokens = re.split(r"[\s-]+", t)
    value = 0.0
    temp = 0.0
    for tok in tokens:
        if tok in _NUMBER_WORDS:
            val = _NUMBER_WORDS[tok]
            if val >= 100:
                temp = max(1, temp) * val
            else:
                temp += val
        else:
            # unknown token, abort fallback
            return None
    value += temp
    return value if value > 0 else None


# ---------------------------------------------------------------------------
# NLU Parsers: intent classifier + slot extractors (LLM-first, deterministic fallback)
# ---------------------------------------------------------------------------

def deterministic_intent_guess(text: str, stage: LoanStage) -> Tuple[str, str]:
    """
    Quick rule-based intent guess when LLM is not available.
    Returns (intent, short_reply_hint).
    Intents: SLOT_VALUE, META, PROCESS, CONFUSION, OUT_OF_SCOPE, CHITCHAT
    """
    t = text.lower().strip()
    # empty or only filler
    if len(t) == 0:
        return "CONFUSION", "I didn't catch that. Could you repeat briefly?"
    # meta keywords
    if any(k in t for k in ["what does", "what is this", "how does", "how do", "who are you", "what are you"]):
        return "META", "I help people apply for personal loans. I can guide you through the process in chat."
    if any(k in t for k in ["why", "for what", "what for", "why do you"]):
        return "PROCESS", "I'm asking for consent so I can process your loan details (basic info, checks)."
    # consent-like
    if any(k in t for k in ["yes", "no", "agree", "i do", "ok", "okay", "sure", "maybe", "i guess", "probably"]):
        # treat as possible consent/confusion depending on presence of 'maybe' variants
        if any(k in t for k in ["maybe", "i guess", "probably", "might"]):
            return "CONFUSION", "Are you leaning towards yes or no?"
        return "SLOT_VALUE", ""
    # amount patterns presence
    if re.search(r"\d+|\blakh\b|\bthousand\b|\bmillion\b|\bcrore\b|\bcr\b|\bk\b|\bm\b", t):
        return "SLOT_VALUE", ""
    # small talk
    if any(k in t for k in ["hi", "hello", "thanks", "thank you"]):
        return "CHITCHAT", "Hi! I can help with loans."
    # default to OUT_OF_SCOPE
    return "OUT_OF_SCOPE", "I’m sorry, I can only help with loan-related questions here."

def classify_intent_llm(user_text: str, stage: LoanStage) -> Tuple[str, str]:
    """
    Intent classifier using LLM. Returns (intent, short_reply_hint).
    Attempts JSON output. Fallbacks to deterministic_intent_guess if LLM unavailable.
    """
    # Keep the prompt strict: want JSON with keys 'intent' and 'reply'
    prompt = f"""
You are an intent classifier for a bank loan assistant.

User utterance:
\"\"\"{user_text}\"\"\"

Current stage: {stage}

Return a JSON object with keys:
- intent: one of "SLOT_VALUE", "META", "PROCESS", "CONFUSION", "OUT_OF_SCOPE", "CHITCHAT"
- reply: a single short sentence (2 lines max) the assistant can say if the intent is not SLOT_VALUE

Example:
{{"intent":"META", "reply":"I help users apply for personal loans via chat."}}

Return EXACTLY the JSON and nothing else.
"""
    obj = None
    parsed = call_llm_json(prompt, temperature=0.0, max_tokens=120)
    if parsed and isinstance(parsed, dict) and "intent" in parsed:
        intent = parsed.get("intent")
        reply = parsed.get("reply", "")
        if intent and isinstance(intent, str):
            # basic validation
            if intent not in {"SLOT_VALUE", "META", "PROCESS", "CONFUSION", "OUT_OF_SCOPE", "CHITCHAT"}:
                return deterministic_intent_guess(user_text, stage)
            return intent, reply or ""
    # fallback
    return deterministic_intent_guess(user_text, stage)

# Slot extraction

def extract_amount(user_text: str, stage: LoanStage) -> Optional[int]:
    """
    Primary NLU for amount. Try LLM-JSON extraction first, fallback to deterministic parsing.
    Returns integer INR value or None.
    """
    # LLM prompt asking for JSON amount
    prompt = f"""
Extract the amount in INR from the user's text.

User text:
\"\"\"{user_text}\"\"\"

Return ONLY valid JSON:
{{"amount": number}}  or {{"amount": null}}

Guidelines:
- Interpret 'lakh' as 100000, 'crore' as 10000000, 'million' as 1000000
- Accept short forms like '100k', '1m', '.9 million'
- If ambiguous, return null
"""
    parsed = call_llm_json(prompt, temperature=0.0, max_tokens=80)
    if parsed and isinstance(parsed, dict) and "amount" in parsed:
        a = parsed["amount"]
        try:
            if a is None:
                pass
            elif isinstance(a, (int, float)):
                val = int(float(a))
                return val
        except Exception:
            pass
    # fallback deterministic parser attempts
    # try direct numeric extraction with units
    t = user_text.lower().replace(",", "").strip()
    # patterns like '100k', '1m'
    m = re.search(r"([\d\.]+)\s*(k|m|cr|crore|lakh|million|billion|thousand)\b", t)
    if m:
        num = float(m.group(1))
        unit = m.group(2)
        unit = unit.lower()
        mult = _WORD_UNITS.get(unit, None)
        if mult:
            val = int(num * mult)
            return val
    # patterns with unit word after or number alone
    # try words_to_number
    wn = words_to_number(t)
    if wn is not None:
        return int(wn)
    # try find plain integers
    m2 = re.search(r"\b(\d{1,9})\b", t)
    if m2:
        try:
            return int(m2.group(1))
        except Exception:
            pass
    return None

def extract_customer_id(user_text: str) -> Optional[str]:
    t = user_text.strip().upper()
    if re.fullmatch(r"CUST\d{3}", t):
        return t
    # try to find pattern anywhere
    m = re.search(r"(CUST\d{3})", user_text.upper())
    if m:
        return m.group(1)
    return None

def extract_consent(user_text: str) -> Optional[bool]:
    """
    LLM-first consent extraction with deterministic fallback.
    Returns True / False / None
    """
    # If clear tokens present, honor them
    t = user_text.lower()
    if re.search(r"\byes\b|\byep\b|\bok\b|\bokay\b|\bi do\b|\bi agree\b|\bagree\b|\bsure\b", t):
        return True
    if re.search(r"\bno\b|\bnope\b|\bdon't\b|\bdo not\b|\bnot\b", t):
        return False
    # LLM as last resort (JSON)
    prompt = f"""
Decide if the user is consenting to proceed with a loan application.

User text:
\"\"\"{user_text}\"\"\"

Return ONLY JSON:
{{"consent": true}} or {{"consent": false}} or {{"consent": null}}
"""
    parsed = call_llm_json(prompt, temperature=0.0, max_tokens=64)
    if parsed and isinstance(parsed, dict) and "consent" in parsed:
        c = parsed.get("consent")
        if c is True:
            return True
        if c is False:
            return False
    return None

# ---------------------------------------------------------------------------
# Response composer and retry escalation
# - Each stage has a set of templates for retries
# - Templates include placeholders
# - Composer uses LLM to rephrase a template (best-effort), otherwise uses templates directly
# ---------------------------------------------------------------------------

# Templates per stage: list of strings; composer chooses index according to retry count
TEMPLATES = {
    "CONSENT": [
        "I need your consent to process basic loan checks (ID & credit bureau). Please say YES to continue or NO to stop.",
        "Before I proceed, please confirm that I can process your loan request (reply YES/NO).",
        "Quick confirm: may I proceed with checking your details for the loan? A simple YES works.",
        "I can only continue with a clear YES. If you'd like help from a human instead, say 'human'.",
    ],
    "AMOUNT_OUT_OF_RANGE": [
        "That amount is outside our supported personal loan range (max ₹10,00,000). Please enter an amount up to ₹10,00,000.",
        "We generally offer personal loans up to ₹10,00,000. Could you pick a lesser amount?",
        "Too high for our product — keep it under ₹10L and I'll continue.",
        "Let's be realistic — max personal loan is ₹10,00,000. Please choose a smaller amount."
    ],
    "AMOUNT_UNCLEAR": [
        "I didn't quite catch the amount. You can say '4 lakh' or '400000'.",
        "Please state the amount clearly: e.g., '₹4 lakh' or '4,00,000'.",
        "Could you rephrase the amount? Try '1 lakh', '2.5 lakh', or '400000'.",
        "I'm still not sure about the amount. If you'd like help, say 'help with amounts'."
    ],
    "CUSTOMER_ID": [
        "Please provide your Customer ID in the format CUST001.",
        "I need your Customer ID (e.g., CUST001) to fetch your profile.",
        "Tell me your Customer ID (CUSTxyz). I'll look up your profile.",
    ],
    "OUT_OF_SCOPE": [
        "I can only help with personal loan applications. For other topics, please contact support.",
        "Sorry, that's out of my scope — I handle loan origination matters.",
    ],
    "META_SHORT": [
        "I assist users through a conversational loan application — short checks and eligibility.",
        "This bot guides you through an AI-assisted personal loan application in chat.",
    ],
}

def rephrase_template(stage_key: str, attempt: int, core: str) -> str:
    """
    Choose a template and optionally ask LLM to rephrase it to sound more human.
    attempt = 1..n (1-based)
    core = the fallback core message if LLM unavailable
    """
    templates = TEMPLATES.get(stage_key, [core])
    idx = min(attempt - 1, len(templates) - 1)
    chosen = templates[idx]
    # Try to rephrase with LLM for naturalness and variable tone (funny/sarcastic on later attempts)
    # Construct a short rephraser prompt - keep it safe: ask for 1-2 lines only
    tone = "friendly"
    if attempt >= 3:
        tone = "playful and slightly sarcastic"
    prompt = f"""
Rewrite the following exactly in 1-2 short lines in a {tone} tone. Do NOT add new instructions.
Text:
\"\"\"{chosen}\"\"\"
Return only the rewritten text.
"""
    out = call_llm_raw(prompt, temperature=0.5, max_tokens=40)
    if out:
        # Always prefer LLM output if short
        short = out.strip().splitlines()[0]
        return short + ("" if "\n" not in out else "\n" + out.splitlines()[1])
    return chosen if core is None else core

# ---------------------------------------------------------------------------
# Small in-memory audit log (for debugging and traceability)
# ---------------------------------------------------------------------------
_AUDIT_LOG = []


def audit_log(entry: Dict[str, Any]) -> None:
    record = {"ts": int(time.time()), **entry}
    _AUDIT_LOG.append(record)
    # keep log small in memory
    if len(_AUDIT_LOG) > 5000:
        _AUDIT_LOG.pop(0)


# ---------------------------------------------------------------------------
# Worker functions
# Each returns a dict:
#   { "next_stage": LoanStage.*, "message": str, "updates": { ... } }
# ---------------------------------------------------------------------------

# Greeting worker
def greeting_worker(state) -> Dict[str, Any]:
    audit_log({"event": "greeting_worker_called", "session": getattr(state, "session_id", None)})
    core = "Hi — I can help you apply for a personal loan. I will ask for a few details and run checks."
    message = rephrase_template("META_SHORT", 1, core)
    return {"next_stage": LoanStage.CONSENT, "message": message, "updates": {}}


# Consent worker: uses extract_consent then behavior depending on agreement
def consent_worker(state, user_input: str) -> Dict[str, Any]:
    audit_log({"event": "consent_worker_called", "input": user_input, "session": getattr(state, "session_id", None)})
    # maintain retry counts
    state.__dict__.setdefault("_retries", {})
    state._retries["CONSENT"] = state._retries.get("CONSENT", 0) + 1
    attempt = state._retries["CONSENT"]

    # classify the message first using the intent classifier (LLM then fallback)
    intent, hint = classify_intent_llm(user_input, state.stage)
    audit_log({"event": "consent_intent", "intent": intent, "hint": hint})

    # If user asked META or PROCESS, give short answer then re-ask consent
    if intent in ("META", "PROCESS"):
        short = hint or "I need your permission to process basic loan checks (ID & bureau)."
        core = rephrase_template("CONSENT", attempt, short)
        composed = f"{short}\n\n{core}"
        audit_log({"event": "consent_meta_answered", "reply": composed})
        return {"next_stage": LoanStage.CONSENT, "message": composed, "updates": {}}

    # Try to extract consent using deterministic + LLM fallback
    consent_val = extract_consent(user_input)
    audit_log({"event": "consent_parsed", "consent": consent_val})

    if consent_val is True:
        msg = "Great — thanks for confirming. Please provide your Customer ID (e.g. CUST001)."
        # reset consent retries to allow later use
        state._retries["CONSENT"] = 0
        return {"next_stage": LoanStage.COLLECT_CUSTOMER_ID, "message": msg, "updates": {}}
    elif consent_val is False:
        # user refused — do not continue; ask if they'd like help or to stop
        msg = "Understood. We won't proceed without your consent. If you change your mind, say YES."
        return {"next_stage": LoanStage.CONSENT, "message": msg, "updates": {}}
    else:
        # UNCLEAR; escalate tone by attempt
        core = rephrase_template("CONSENT", attempt, TEMPLATES["CONSENT"][min(attempt - 1, len(TEMPLATES["CONSENT"]) - 1)])
        # If we've already asked many times, be firmer and offer help
        if attempt >= 4:
            core = "I need a clear YES to proceed. If you are unsure, reply 'help' or 'speak to human'."
        return {"next_stage": LoanStage.CONSENT, "message": core, "updates": {}}


# Customer ID worker
def customer_id_worker(state, user_input: str) -> Dict[str, Any]:
    audit_log({"event": "customer_id_worker_called", "input": user_input})
    # classify intent
    intent, hint = classify_intent_llm(user_input, state.stage)
    if intent != "SLOT_VALUE":
        # answer/question first then redirect
        short = hint or "I need your Customer ID to fetch your profile."
        composed = respond_and_redirect(user_input=user_input, quick=short, redirect="Please give your Customer ID (e.g., CUST001).")
        return {"next_stage": LoanStage.COLLECT_CUSTOMER_ID, "message": composed, "updates": {}}

    cid = extract_customer_id(user_input)
    if not cid:
        return {"next_stage": LoanStage.COLLECT_CUSTOMER_ID, "message": rephrase_template("CUSTOMER_ID", 1, "Please provide Customer ID in format CUST001."), "updates": {}}

    # valid id
    return {"next_stage": LoanStage.COLLECT_AMOUNT, "message": "Customer ID recorded. How much loan amount do you need?", "updates": {"customer_id": cid}}


# Amount worker: parse first, then validate against product rules
MAX_LOAN = 1_000_000  # ₹10,00,00o (10 lakh) example; change to 10 lakh -> 1_000_000? Keep as per existing settings
def amount_worker(state, user_input: str) -> Dict[str, Any]:
    audit_log({"event": "amount_worker_called", "input": user_input})
    state.__dict__.setdefault("_retries", {})
    state._retries["AMOUNT"] = state._retries.get("AMOUNT", 0) + 1
    attempt = state._retries["AMOUNT"]

    # first classify intent
    intent, hint = classify_intent_llm(user_input, state.stage)
    if intent != "SLOT_VALUE":
        short = hint or "I need the loan amount to proceed."
        composed = respond_and_redirect(user_input=user_input, quick=short, redirect="Please tell me the loan amount you want (e.g., 4 lakh).")
        return {"next_stage": LoanStage.COLLECT_AMOUNT, "message": composed, "updates": {}}

    # Try NLU extraction (LLM first, then fallback)
    amt = extract_amount(user_input, state.stage)
    if amt is None:
        # unclear: use templates and rephrase
        message = rephrase_template("AMOUNT_UNCLEAR", attempt, TEMPLATES["AMOUNT_UNCLEAR"][0])
        return {"next_stage": LoanStage.COLLECT_AMOUNT, "message": message, "updates": {}}

    # normalize & validate numeric range and sanity checks
    # sanity: must be > 5000 and <= MAX_LOAN (customize)
    if amt <= 0:
        message = "That doesn't look like a valid amount. Try again with numbers only or '4 lakh'."
        return {"next_stage": LoanStage.COLLECT_AMOUNT, "message": message, "updates": {}}
    if amt > MAX_LOAN:
        # out of range; progressive messaging via rephrase_template
        message = rephrase_template("AMOUNT_OUT_OF_RANGE", attempt, TEMPLATES["AMOUNT_OUT_OF_RANGE"][0])
        return {"next_stage": LoanStage.COLLECT_AMOUNT, "message": message, "updates": {}}

    # success
    return {"next_stage": LoanStage.CRM_CHECK, "message": f"Understood — you requested ₹{amt}. Checking your profile now.", "updates": {"requested_amount": int(amt)}}


# CRM worker
def crm_worker(state) -> Dict[str, Any]:
    audit_log({"event": "crm_worker_called", "customer_id": getattr(state, "customer_id", None)})
    try:
        profile = get_crm_profile(state.customer_id) if getattr(state, "customer_id", None) else None
    except Exception as e:
        profile = None
    # short human-friendly message then proceed
    msg = "Internal profile lookup complete." if profile else "No internal profile found; proceeding with available info."
    return {"next_stage": LoanStage.BUREAU_CHECK, "message": msg + " Now reviewing credit bureau details.", "updates": {"crm_profile": profile}}


# Bureau worker
def bureau_worker(state) -> Dict[str, Any]:
    audit_log({"event": "bureau_worker_called", "customer_id": getattr(state, "customer_id", None)})
    try:
        bureau = get_bureau_report(state.customer_id) if getattr(state, "customer_id", None) else None
    except Exception:
        bureau = None
    msg = "Credit bureau review completed." if bureau else "No bureau report available; proceeding with limited info."
    return {"next_stage": LoanStage.UNDERWRITING, "message": msg + " Evaluating eligibility now.", "updates": {"bureau_report": bureau}}


# Underwriting worker
def underwriting_worker(state) -> Dict[str, Any]:
    audit_log({"event": "underwriting_worker_called", "session": getattr(state, "session_id", None)})
    try:
        result = evaluate_application(customer_profile=state.crm_profile, bureau_report=state.bureau_report, requested_amount=state.requested_amount)
    except Exception as e:
        # If underwriting throws, escalate
        audit_log({"event": "underwriting_failed", "error": str(e)})
        return {"next_stage": LoanStage.ESCALATED, "message": "There was a problem evaluating your application; we'll escalate this to a human reviewer.", "updates": {}}
    # produce short message
    return {"next_stage": LoanStage.DECISION, "message": "Underwriting completed. Preparing final decision.", "updates": {"underwriting_result": result}}


# Decision worker
def decision_worker(state) -> Dict[str, Any]:
    audit_log({"event": "decision_worker_called", "session": getattr(state, "session_id", None)})
    result = getattr(state, "underwriting_result", None)
    if not result:
        return {"next_stage": LoanStage.ESCALATED, "message": "Decision could not be made automatically; escalating to manual review.", "updates": {}}
    dec = result.get("decision")
    if dec == "approve":
        approved_amount = result.get("approved_amount", result.get("requested_amount", 0))
        msg = f"Congratulations — your loan has been approved for ₹{approved_amount}. We will send details shortly."
        return {"next_stage": LoanStage.COMPLETED, "message": msg, "updates": {}}
    elif dec == "reject":
        reason = result.get("reason", "Not meeting lending criteria.")
        msg = f"Unfortunately your application was declined. Reason: {reason}"
        return {"next_stage": LoanStage.COMPLETED, "message": msg, "updates": {}}
    else:
        # escalate
        return {"next_stage": LoanStage.ESCALATED, "message": "Your case requires manual review. Our team will contact you.", "updates": {}}


# ---------------------------------------------------------------------------
# Small utility used in some paths - creates short reply then redirects
# ---------------------------------------------------------------------------
def respond_and_redirect(user_input: str, quick: str, redirect: str) -> str:
    """
    Compose a two-part response:
    - A short direct answer to the user's question (quick)
    - A redirect/prompt to return to the active task (redirect)
    Keep total output short (1-3 lines).
    Try to rephrase quick using LLM if available.
    """
    # try slight rephrase of quick with LLM but ensure length
    prompt = f"""
Rewrite this reply in 1-2 short lines. Do not add new instructions.
Text:
\"\"\"{quick}\"\"\"
"""
    out = call_llm_raw(prompt, temperature=0.5, max_tokens=40)
    if out:
        quick_r = out.strip().splitlines()[0]
    else:
        quick_r = quick
    return f"{quick_r}\n\n{redirect}"


# ---------------------------------------------------------------------------
# Expose a small helper mapping functions for run_stage compatibility,
# so run_stage can call these functions exactly as before.
# ---------------------------------------------------------------------------

# The run_stage() function should import these functions by name (as your current run_stage does).
# Example:
# from app.graph.workers import greeting_worker, consent_worker, ...
# The names below must match the imports used elsewhere.
# ---------------------------------------------------------------------------

# ensure names are available
__all__ = [
    "greeting_worker" ,
    "consent_worker" ,
    "customer_id_worker" ,
    "amount_worker" ,
    "crm_worker" ,
    "bureau_worker" ,
    "underwriting_worker" ,
    "decision_worker" ,
]
