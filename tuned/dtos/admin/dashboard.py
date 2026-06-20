from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class AdminKPIDTO:
    active_orders: int
    total_revenue: float
    total_clients: int
    pending_actions: int

@dataclass
class SpendingVelocityDTO:
    month: str
    amount: float

@dataclass
class ChartDataDTO:
    name: str
    value: int

@dataclass
class AdminDashboardAnalyticsDTO:
    spending_velocity: list[SpendingVelocityDTO]
    project_lifecycle: list[ChartDataDTO]
    service_mix: list[ChartDataDTO]
    referral_growth: list[ChartDataDTO]

@dataclass
class AdminUpcomingDeadlineDTO:
    id: str
    order_number: str
    title: Optional[str]
    due_date: str
    priority: str

@dataclass
class AdminActivityFeedEntryDTO:
    id: str
    action: str
    entity_type: str
    entity_id: str
    created_at: str

@dataclass
class AdminDashboardTrackingDTO:
    upcoming_deadlines: list[AdminUpcomingDeadlineDTO]
    activity_feed: list[AdminActivityFeedEntryDTO]

@dataclass
class ActionableAlertDTO:
    id: str
    type: str
    message: str
    metadata: dict[str, str] = field(default_factory=dict)
    created_at: str = ""

@dataclass
class AdminDashboardAlertsDTO:
    alerts: list[ActionableAlertDTO]
