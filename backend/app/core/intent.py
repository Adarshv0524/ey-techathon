def is_faq_intent(text: str) -> bool:
    text = text.lower()
    faq_keywords = [
        "interest rate",
        "emi",
        "tenure",
        "prepayment",
        "charges",
        "penalty",
        "policy"
    ]
    return any(keyword in text for keyword in faq_keywords)
