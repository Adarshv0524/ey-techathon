# app/api/mock_services.py

from fastapi import APIRouter, HTTPException
from app import mock_services

router = APIRouter()


@router.get("/mock/crm/{customer_id}")
def crm(customer_id: str):
    profile = mock_services.get_crm_profile(customer_id)
    if not profile:
        raise HTTPException(404, "Customer not found")
    return profile


@router.get("/mock/bureau/{customer_id}")
def bureau(customer_id: str):
    report = mock_services.get_bureau_report(customer_id)
    if not report:
        raise HTTPException(404, "Bureau report not found")
    return report
