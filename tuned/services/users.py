from typing import Optional
from tuned.core.exceptions import InvalidCredentials, ServiceError
from tuned.repository import repositories

class UserService:
    def __init__(self):
        self._repo = repositories.user
    
    def check_new_user_referral(self, referrer_code: Optional[str]) -> bool:
        try:
            if not referrer_code:
                return False
            referrer = self._repo.get_by_referral_code(referrer_code)
            if not referrer:
                raise InvalidCredentials("Referral code is invalid")
            return True
        except InvalidCredentials as e:
            raise e
        except Exception as e:
            raise ServiceError(f"Error while fetching user by referral code: {str(e)}") from e
        
userService = UserService()