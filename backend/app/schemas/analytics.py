from typing import Dict, List
from pydantic import BaseModel


class MonthlyTrendPoint(BaseModel):
    month: str
    amount: float
    count: int


class AnalyticsSummaryResponse(BaseModel):
    total_patients: int
    total_revenue: float
    paid_sessions: int
    new_patients: int
    condition_distribution: Dict[str, int]
    revenue_by_month: List[MonthlyTrendPoint]
    patients_by_month: List[MonthlyTrendPoint]
