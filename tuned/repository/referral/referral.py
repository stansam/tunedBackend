from typing import Optional, List
from sqlalchemy.exc import SQLAlchemyError
from tuned.models.referral import Referral
from tuned.models.enums import ReferralStatus
from tuned.extensions import db
from tuned.core.logging import get_logger
from tuned.models.referral import Referral
from tuned.utils.variables import Variables
from tuned.repository.exceptions import DatabaseError
from tuned.repository.utils import build_month_window
from datetime import datetime, timezone
from sqlalchemy import func, asc
from sqlalchemy.orm import Session
from typing import Dict
from flask import current_app
import logging


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

class ReferralRepository:
    def __init__(self):
        self.session = db.session
        self.Referral = Referral

    def create(self, referrer_id: str, referred_id: str, code: str, commission: float = 0.0) -> Referral:
        try:
            referral = Referral(
                referrer_id=referrer_id,
                referred_id=referred_id,
                code=code,
                commission=commission,
                status=ReferralStatus.PENDING
            )
            self.session.add(referral)
            self.session.flush()
            return referral
        except SQLAlchemyError as e:
            logger.error(f"[ReferralRepository] Error creating referral: {e}")
            raise

    def get_by_id(self, id: str) -> Optional[Referral]:
        return self.session.query(Referral).filter_by(id=id).first()

    def get_by_referred_id(self, referred_id: str) -> Optional[Referral]:
        return self.session.query(Referral).filter_by(referred_id=referred_id).first()

    def get_by_code(self, code: str) -> Optional[Referral]:
        return self.session.query(Referral).filter_by(code=code).first()

    def get_active_by_referrer(self, referrer_id: str) -> List[Referral]:
        return self.session.query(Referral).filter(
            Referral.referrer_id == referrer_id,
            Referral.status.in_([ReferralStatus.PENDING, ReferralStatus.ACTIVE])
        ).all()

    def update_commission_and_status(self, id: str, added_commission: float, status: ReferralStatus) -> Optional[Referral]:
        try:
            referral = self.get_by_id(id)
            if not referral:
                return None
            
            referral.commission = referral.commission + added_commission
            referral.status = status
            self.session.flush()
            return referral
        except SQLAlchemyError as e:
            logger.error(f"[ReferralRepository] Error updating commission: {e}")
            raise
    
    def get_referral_growth(
        self, referrer_id: str, months: int = 6
    ) -> list[tuple[str, float]]:
        return GetReferralGrowth(self.session).execute(referrer_id, months)


# import logging
# from sqlalchemy.orm import Session
# from sqlalchemy import func, asc
# from sqlalchemy.exc import SQLAlchemyError
# from datetime import datetime, timezone
# from tuned.extensions import current_app
# from tuned.models.enums import Variables
# from tuned.repository.utils import build_month_window
# from tuned.repository.exceptions import DatabaseError
# from typing import Dict
# from tuned.core.logging import get_logger
# from tuned.models import Referral
# from tuned.utils.variables import Variables



