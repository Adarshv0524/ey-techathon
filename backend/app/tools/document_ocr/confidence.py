def compute_confidence(data: dict) -> float:
    total = len(data)
    filled = sum(1 for v in data.values() if v)

    return round(filled / total, 2)
