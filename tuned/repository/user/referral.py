import logging
from sqlalchemy.orm import Session
from sqlalchemy import func, asc
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
from tuned.models.user import Referral
from tuned.extensions import current_app
from tuned.models.enums import Variables
from tuned.repository.utils import build_month_window
from tuned.repository.exceptions import DatabaseError
from typing import Dict
from tuned.core.logging import get_logger
from tuned.models import Referral
from tuned.utils.variables import Variables

logger: logging.Logger = get_logger(__name__)

class GetReferralGrowth:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _month_label_expr(self, column: object) -> object:
        if current_app.config["FLASK_ENV"] == Variables.PRODUCTION:
            return func.to_char(column, "YYYY-MM")
        return func.strftime("%Y-%m", column)

    def execute(self, referrer_id: str, months: int = 6) -> list[tuple[str, float]]:
        try:
            month_expr = self._month_label_expr(Referral.created_at)
            rows = (
                self.db.query(month_expr, func.sum(Referral.commission))
                .filter(Referral.referrer_id == referrer_id)
                .group_by(month_expr)
                .order_by(asc(month_expr))
                .all()
            )
            now = datetime.now(timezone.utc)
            window: Dict[str, float] = build_month_window(now, months)
            for label, total in rows:
                if label in window:
                    window[label] = float(total or 0.0)
            return list(window.items())
        except SQLAlchemyError as exc:
            logger.error("[GetReferralGrowth] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc