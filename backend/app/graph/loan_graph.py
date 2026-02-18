#backend/app/graph/loan_graph.py

from app.core.session import LoanStage
from app.graph.workers import (
    greeting_worker,
    consent_worker,
    customer_id_worker,
    amount_worker,
    crm_worker,
    bureau_worker,
    underwriting_worker,
    decision_worker
)


def run_stage(state, user_input=None):
    if state.stage == LoanStage.GREETING:
        return greeting_worker(state)

    if state.stage == LoanStage.CONSENT:
        return consent_worker(state, user_input)

    if state.stage == LoanStage.COLLECT_CUSTOMER_ID:
        return customer_id_worker(state, user_input)

    if state.stage == LoanStage.COLLECT_AMOUNT:
        return amount_worker(state, user_input)

    if state.stage == LoanStage.CRM_CHECK:
        return crm_worker(state)

    if state.stage == LoanStage.BUREAU_CHECK:
        return bureau_worker(state)

    if state.stage == LoanStage.UNDERWRITING:
        return underwriting_worker(state)

    if state.stage == LoanStage.DECISION:
        return decision_worker(state)

    return None
