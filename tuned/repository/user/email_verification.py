from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from tuned.models import User
from tuned.repository.user.get import GetUserByID, GetUserByEmail
from tuned.repository.exceptions import NotFound, DatabaseError, AlreadyExists


_TOKEN_EXPIRES_HOURS = 24
_TOKEN_BYTES = 32


def _hash_token(raw_token: str) -> str:
    return hashlib.blake2b(raw_token.encode(), digest_size=32).hexdigest()


class GenerateAndStoreVerificationToken:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, user_id: str) -> tuple[User, str]:
        try:
            user: User = GetUserByID(self.session).execute(user_id)
        except NotFound:
            raise NotFound("User not found") from None

        if user.email_verified:
            raise AlreadyExists("Email is already verified")

        raw_token = secrets.token_urlsafe(_TOKEN_BYTES)
        hashed = _hash_token(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=_TOKEN_EXPIRES_HOURS)

        try:
            user.email_verification_token = hashed
            user.email_verification_token_expires_at = expires_at
            self.session.add(user)
            self.session.commit()
            self.session.refresh(user)
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseError(
                f"DB error while generating verification token for user {user_id}: {exc}"
            ) from exc

        return user, raw_token


class ConfirmEmailVerification:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, user_id: str, raw_token: str) -> User:
        try:
            user: User = GetUserByID(self.session).execute(user_id)
        except NotFound:
            raise NotFound("User not found") from None

        if user.email_verified:
            raise AlreadyExists("Email is already verified")

        expires_at = user.email_verification_token_expires_at
        if expires_at is None:
            raise ValueError("no_token")

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if datetime.now(timezone.utc) > expires_at:
            raise ValueError("expired")

        stored_hash = user.email_verification_token or ""
        incoming_hash = _hash_token(raw_token)
        if not hmac.compare_digest(stored_hash, incoming_hash):
            raise ValueError("invalid")

        try:
            user.email_verified = True
            user.email_verification_token = None
            user.email_verification_token_expires_at = None
            self.session.add(user)
            self.session.commit()
            self.session.refresh(user)
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseError(
                f"DB error while confirming verification for user {user_id}: {exc}"
            ) from exc

        return user


class GetUserForResend:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, email: str) -> User | None:
        try:
            return GetUserByEmail(self.session).execute(email)
        except NotFound:
            return None
