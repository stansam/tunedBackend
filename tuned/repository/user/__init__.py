from tuned.models import User
from tuned.dtos import CreateUserDTO, UpdateUserDTO, ActionableAlertDTO
from tuned.repository.user.create import CreateUser
from tuned.repository.user.get import GetUserByEmail, GetUserByID, GetAdminUser, GetUserByUsername, GetUserByReferralCode
from tuned.repository.user.update import UpdateUser
from tuned.repository.user.email_verification import (
    GenerateAndStoreVerificationToken,
    ConfirmEmailVerification,
    GetUserForResend,
)
# from tuned.repository.user.referral import GetReferralGrowth
from tuned.repository.user.alerts import GetActionableAlerts
from tuned.extensions import db
import string

class UserRepository: 
    def __init__(self) -> None:
        self.db = db  
    def create_user(self, user_data: CreateUserDTO) -> User:
        return CreateUser(self.db.session).execute(user_data)
    def get_user_by_id(self, user_id: string) -> User:
        return GetUserByID(self.db.session).execute(user_id)
    def get_user_by_email(self, email: string) -> User:
        return GetUserByEmail(self.db.session).execute(email)
    def get_user_by_username(self, username: string) -> User:
        return GetUserByUsername(self.db.session).execute(username)
    def get_by_referral_code(self, referral_code: string) -> User | None:
        return GetUserByReferralCode(self.db.session).execute(referral_code)
    def get_admin_user(self) -> User:
        return GetAdminUser(self.db.session).execute()
    def update_user(self, updates: UpdateUserDTO, actor_id: string) -> User:
        return UpdateUser(self.db.session).execute(updates, actor_id=actor_id)
    def increment_failed_login_attempts(self, user_id: string) -> int:
        return UpdateUser(self.db.session).increment_failed_login_attempts(user_id)

    def generate_verification_token(self, user_id: str) -> tuple[User, str]:
        return GenerateAndStoreVerificationToken(self.db.session).execute(user_id)

    def confirm_email_verification(self, user_id: str, raw_token: str) -> User:
        return ConfirmEmailVerification(self.db.session).execute(user_id, raw_token)

    def get_user_for_resend(self, email: str) -> User | None:
        return GetUserForResend(self.db.session).execute(email)
    
    def get_actionable_alerts(self, client_id: str) -> list[ActionableAlertDTO]:
        return GetActionableAlerts(self.db.session).execute(client_id)