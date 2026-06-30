from datetime import datetime, date


def generate_priority(deadline):
    """
    Returns HIGH, MEDIUM, or LOW based on deadline.
    """

    if isinstance(deadline, str):
        deadline = datetime.strptime(deadline, "%Y-%m-%d").date()

    today = date.today()

    days_left = (deadline - today).days

    if days_left <= 3:
        return "HIGH"

    elif days_left <= 21:
        return "MEDIUM"

    else:
        return "LOW"