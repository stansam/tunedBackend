from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from tuned.dtos.order import OrderProgressDTO, UpcomingDeadlineDTO

@dataclass
class NavStatsDTO:
    active_orders: int
    balance: float  # TODO: implement wallet balance calculation

@dataclass
class DashboardKPIDTO:
    active_projects: int
    portfolio_value: float
    reward_points:   int
    next_deadline:   Optional[str]

@dataclass
class SpendingVelocityDTO:
    month:  str    # "YYYY-MM"
    amount: float

@dataclass
class ChartDataDTO:
    name:  str
    value: float

@dataclass
class DashboardAnalyticsDTO:
    spending_velocity: list[SpendingVelocityDTO]
    project_lifecycle: list[ChartDataDTO]
    service_mix:       list[ChartDataDTO]
    referral_growth:   list[ChartDataDTO]

@dataclass
class ActivityFeedEntryDTO:
    id:          str
    action:      str
    entity_type: Optional[str]
    entity_id:   Optional[str]
    created_at:  str

    @classmethod
    def from_model(cls, log: object) -> "ActivityFeedEntryDTO":
        return cls(
            id=str(log.id),
            action=log.action,
            entity_type=log.entity_type,
            entity_id=(
                str(log.entity_id)
                if log.entity_id else None
            ),
            created_at=log.created_at.isoformat(),
        )


@dataclass
class DashboardTrackingDTO:
    latest_order:       Optional[OrderProgressDTO]
    upcoming_deadlines: list[UpcomingDeadlineDTO]
    activity_feed:      list[ActivityFeedEntryDTO]

@dataclass
class ActionableAlertDTO:
    id:         str
    type:       str
    message:    str
    metadata:   dict[str, str] = field(default_factory=dict)
    created_at: str = ""


@dataclass
class DashboardAlertsDTO:
    alerts: list[ActionableAlertDTO]
