# backend/app/underwriting.py

from pathlib import Path
from typing import Dict, Any
import yaml


RULES_PATH = Path(__file__).resolve().parent.parent / "config" / "rules.yaml"


def _load_rules() -> Dict[str, Any]:
    if not RULES_PATH.exists():
        raise FileNotFoundError(f"Underwriting rules file not found at {RULES_PATH}")
    with RULES_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


RULES = _load_rules()


def evaluate_application(
    customer_profile: Dict[str, Any],
    bureau_report: Dict[str, Any],
    requested_amount: int,
) -> Dict[str, Any]:
    """
    Deterministic underwriting decision:
    - Uses score tiers from rules.yaml
    - Uses monthly income and FOIR
    """
    min_credit_score = RULES["min_credit_score"]
    score_tiers = RULES["score_tiers"]
    default_rejection_reason = RULES["default_rejection_reason"]
    max_foir = RULES["max_foir"]
    income_multiplier_cap = RULES["income_multiplier_cap"]

    credit_score = bureau_report.get("credit_score")
    if credit_score is None:
        return {
            "decision": "reject",
            "approved_amount": 0,
            "requested_amount": int(requested_amount),
            "reason": "Missing credit score in bureau report.",
            "metadata": {},
        }

    if credit_score < min_credit_score:
        return {
            "decision": "reject",
            "approved_amount": 0,
            "requested_amount": int(requested_amount),
            "reason": default_rejection_reason,
            "metadata": {
                "credit_score": credit_score,
                "min_credit_score": min_credit_score,
            },
        }

    # Find matching tier (highest possible tier where credit_score >= min_score)
    applicable_tier = None
    for tier in sorted(score_tiers, key=lambda t: t["min_score"], reverse=True):
        if credit_score >= tier["min_score"]:
            applicable_tier = tier
            break

    if not applicable_tier:
        # Should not happen if rules are consistent, but safe fallback
        return {
            "decision": "reject",
            "approved_amount": 0,
            "requested_amount": int(requested_amount),
            "reason": "No applicable score tier found.",
            "metadata": {"credit_score": credit_score},
        }

    score_ceiling = applicable_tier["max_amount"]
    require_docs = applicable_tier["require_docs"]

    income = customer_profile.get("monthly_income", 0)
    existing_emi = customer_profile.get("existing_emi", 0)

    # Income-based ceiling: e.g., 20x monthly income
    income_ceiling = income * income_multiplier_cap

    # Max eligible amount at all
    max_eligible_amount = min(score_ceiling, income_ceiling)

    if max_eligible_amount <= 0:
        return {
            "decision": "reject",
            "approved_amount": 0,
            "requested_amount": int(requested_amount),
            "reason": "Income-based eligibility is zero.",
            "metadata": {
                "credit_score": credit_score,
                "income": income,
            },
        }

    # FOIR check: approximate EMI as requested_amount / multiplier
    approx_new_emi = requested_amount / income_multiplier_cap
    foir = (existing_emi + approx_new_emi) / income if income > 0 else 1.0

    decision = "approve"
    reason = "Eligible as per credit score and income."
    approved_amount = min(requested_amount, max_eligible_amount)

    if foir > max_foir:
        decision = "need_docs"
        reason = (
            f"FOIR {foir:.2f} exceeds max {max_foir:.2f}. Requires documents/manual review."
        )

    if require_docs and decision == "approve":
        decision = "need_docs"
        reason = (
            f"Score tier requires income proof. Credit score {credit_score}, "
            f"tier min_score {applicable_tier['min_score']}."
        )

    return {
        "decision": decision,
        "approved_amount": int(approved_amount),
        "requested_amount": int(requested_amount),
        "reason": reason,
        "metadata": {
            "credit_score": credit_score,
            "tier_min_score": applicable_tier["min_score"],
            "score_ceiling": score_ceiling,
            "income": income,
            "income_ceiling": income_ceiling,
            "existing_emi": existing_emi,
            "max_foir": max_foir,
            "foir": foir,
            "require_docs": require_docs,
        },
    }
