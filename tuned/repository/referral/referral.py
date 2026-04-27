from typing import Optional, List
from sqlalchemy.exc import SQLAlchemyError
from tuned.models.referral import Referral
from tuned.models.enums import ReferralStatus
from tuned.extensions import db
from tuned.core.logging import get_logger
from tuned.dtos.referral import ReferralResponseDTO
from tuned.utils.variables import Variables
from tuned.repository.exceptions import DatabaseError
from tuned.repository.utils import build_month_window
from datetime import datetime, timezone
from sqlalchemy import select, func, asc, extract
from tuned.repository.protocols import ReferralRepositoryProtocol
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging


logger: logging.Logger = get_logger(__name__)
class GetReferralGrowth:
    def __init__(self, session: Session) -> None:
        self.session = session

    def _month_label_expr(self, column: Any) -> Any:
        dialect_name = self.session.bind.dialect.name if self.session.bind else "postgresql"
        if dialect_name == "postgresql":
            return func.to_char(column, "YYYY-MM")
        return func.strftime("%Y-%m", column)

    def execute(self, referrer_id: str, months: int = 6) -> list[tuple[str, float]]:
        try:
            month_expr = self._month_label_expr(Referral.created_at)
            stmt = (
                select(month_expr, func.sum(Referral.points_earned))
                .filter(Referral.referrer_id == referrer_id)
                .group_by(month_expr)
                .order_by(asc(month_expr))
            )
            rows = self.session.execute(stmt).all()
            
            now = datetime.now(timezone.utc)
            window: Dict[str, float] = build_month_window(now, months)
            for label, total in rows:
                if label in window:
                    window[label] = float(total or 0)
            return list(window.items())
        except SQLAlchemyError as exc:
            logger.error("[GetReferralGrowth] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc

class ReferralRepository(ReferralRepositoryProtocol):
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, referrer_id: str, referred_id: str, code: str, points_earned: int = 0) -> ReferralResponseDTO:
        try:
            referral = Referral(
                referrer_id=referrer_id,
                referred_id=referred_id,
                code=code,
                points_earned=points_earned,
                status=ReferralStatus.PENDING
            )
            self.session.add(referral)
            self.session.flush()
            return ReferralResponseDTO.from_model(referral)
        except SQLAlchemyError as e:
            logger.error(f"[ReferralRepository] Error creating referral: {e}")
            raise

    def _get_model_by_id(self, id: str) -> Optional[Referral]:
        stmt = select(Referral).where(Referral.id == id)
        return self.session.scalar(stmt)

    def get_by_id(self, id: str) -> Optional[ReferralResponseDTO]:
        model = self._get_model_by_id(id)
        return ReferralResponseDTO.from_model(model) if model else None

    def get_by_referred_id(self, referred_id: str) -> Optional[ReferralResponseDTO]:
        stmt = select(Referral).where(Referral.referred_id == referred_id)
        model = self.session.scalar(stmt)
        return ReferralResponseDTO.from_model(model) if model else None

    def get_by_code(self, code: str) -> Optional[ReferralResponseDTO]:
        stmt = select(Referral).where(Referral.code == code)
        model = self.session.scalar(stmt)
        return ReferralResponseDTO.from_model(model) if model else None

    def get_active_by_referrer(self, referrer_id: str) -> List[ReferralResponseDTO]:
        stmt = select(Referral).where(
            Referral.referrer_id == referrer_id,
            Referral.status.in_([ReferralStatus.PENDING, ReferralStatus.ACTIVE])
        )
        models = self.session.scalars(stmt).all()
        return [ReferralResponseDTO.from_model(m) for m in models]

    def update_points_and_status(
        self, 
        id: str, 
        added_points: int, 
        status: ReferralStatus,
        completed_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None
    ) -> Optional[ReferralResponseDTO]:
        try:
            referral = self._get_model_by_id(id)
            if not referral:
                return None
            
            referral.points_earned = referral.points_earned + added_points
            referral.status = status
            if completed_at:
                referral.completed_at = completed_at
            if expires_at:
                referral.expires_at = expires_at
            self.session.flush()
            return ReferralResponseDTO.from_model(referral)
        except SQLAlchemyError as e:
            logger.error(f"[ReferralRepository] Error updating points: {e}")
            raise

    def count_monthly_completed_referrals(self, referrer_id: str, year: int, month: int) -> int:
        stmt = select(func.count(Referral.id)).where(
            Referral.referrer_id == referrer_id,
            Referral.status == ReferralStatus.COMPLETED,
            extract('year', Referral.completed_at) == year,
            extract('month', Referral.completed_at) == month
        )
        count = self.session.execute(stmt).scalar()
        return count or 0

    def get_referral_growth(
        self, referrer_id: str, months: int = 6
    ) -> list[tuple[str, float]]:
        return GetReferralGrowth(self.session).execute(referrer_id, months)



