import re

def parse_salary_slip(text: str):
    data = {
        "name": None,
        "employer": None,
        "net_salary": None,
        "pay_period": None
    }

    name_match = re.search(r"Name[:\s]+([A-Za-z ]+)", text, re.I)
    if name_match:
        data["name"] = name_match.group(1).strip()

    employer_match = re.search(r"(Company|Employer)[:\s]+(.+)", text, re.I)
    if employer_match:
        data["employer"] = employer_match.group(2).strip()

    salary_match = re.search(r"(Net Salary|Net Pay)[:\s₹]+([\d,]+)", text, re.I)
    if salary_match:
        data["net_salary"] = int(salary_match.group(2).replace(",", ""))

    period_match = re.search(r"(Month|Period)[:\s]+([A-Za-z0-9\- ]+)", text, re.I)
    if period_match:
        data["pay_period"] = period_match.group(2).strip()

    confidence = sum(1 for v in data.values() if v) / 4
    return data, round(confidence, 2)


def parse_id_card(text: str):
    data = {
        "name": None,
        "id_number": None
    }

    name_match = re.search(r"Name[:\s]+([A-Za-z ]+)", text, re.I)
    if name_match:
        data["name"] = name_match.group(1).strip()

    id_match = re.search(r"\b[A-Z]{5}\d{4}[A-Z]\b", text)  # PAN-like
    if id_match:
        data["id_number"] = id_match.group(0)

    confidence = sum(1 for v in data.values() if v) / 2
    return data, round(confidence, 2)
