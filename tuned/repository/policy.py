import uuid
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from tuned.models.policy import UserPolicyAcceptance
from tuned.repository.exceptions import DatabaseError

class PolicyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        user_id: str,
        terms_version: str,
        privacy_version: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> UserPolicyAcceptance:
        try:
            acceptance = UserPolicyAcceptance(
                user_id=uuid.UUID(user_id),
                terms_version=terms_version,
                privacy_version=privacy_version,
                ip_address=ip_address,
                user_agent=user_agent
            )
            self.session.add(acceptance)
            self.session.flush()
            return acceptance
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while recording policy acceptance: {str(e)}") from e

    def get_latest_for_user(self, user_id: str) -> Optional[UserPolicyAcceptance]:
        try:
            stmt = select(UserPolicyAcceptance).where(
                UserPolicyAcceptance.user_id == uuid.UUID(user_id),
                UserPolicyAcceptance.is_deleted == False
            ).order_by(UserPolicyAcceptance.accepted_at.desc())
            return self.session.scalar(stmt)
        except ValueError:
            return None
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching latest user policy acceptance: {str(e)}") from e

    def save(self) -> None:
        try:
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f"Database error while saving policy changes: {str(e)}") from e

    def rollback(self) -> None:
        self.session.rollback()
