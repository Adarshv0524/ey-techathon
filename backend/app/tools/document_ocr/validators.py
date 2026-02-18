def validate_salary_data(data) -> bool:
    return (
        data.name is not None and
        data.employer is not None and
        data.net_salary is not None and
        data.net_salary > 0
    )
