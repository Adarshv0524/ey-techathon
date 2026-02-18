from dataclasses import dataclass
from typing import Optional

@dataclass
class SalarySlipData:
    name: Optional[str]
    employer: Optional[str]
    net_salary: Optional[int]
    pay_period: Optional[str]

@dataclass
class OCRResult:
    doc_type: str
    data: dict
    confidence: float
