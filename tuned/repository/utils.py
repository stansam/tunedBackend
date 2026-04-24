from typing import Dict
from datetime import datetime
from dateutil.relativedelta import relativedelta

# TODO: implement decimal over float
def build_month_window(now: datetime, months: int) -> Dict[str, float]:
    window: Dict[str, float] = {}
    for i in range(months - 1, -1, -1):
        key = (now - relativedelta(months=i)).strftime("%Y-%m")
        window[key] = 0.0
    return window