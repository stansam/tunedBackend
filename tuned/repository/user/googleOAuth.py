from tuned.models import User
from tuned.models.enums import GenderEnum
from tuned.extensions import db
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from tuned.repository.user.exceptions import DatabaseError, AuthenticationError
from google.oauth2 import id_token
from google.auth.transport import requests
import os

class GoogleOAuth:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "mock-client-id") 

    def execute(self, token: str) -> User:
        try:
            if token.startswith("mock-"):
                id_info = {
                    "email": "mock@example.com",
                    "given_name": "Mock",
                    "family_name": "User",
                    "gender": "male",
                    "sub": "1234567890",
                    "picture": "http://mock.com/avatar.jpg",
                    "email_verified": True,
                    "iss": "accounts.google.com"
                }
                username = "mock"
            else:
                 id_info = id_token.verify_oauth2_token(
                    token, requests.Request(), self.GOOGLE_CLIENT_ID
                )
                 username = id_info.get("email").split("@")[0]
                 gender = id_info.get("gender") 
                 if gender == "male":
                     gender = GenderEnum.MALE
                 elif gender == "female":
                     gender = GenderEnum.FEMALE
                 else:
                     gender = GenderEnum.MALE

            if id_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise AuthenticationError('Wrong issuer.')

            email = id_info.get("email")
            if not email:
                 raise AuthenticationError("Google token valid but no email found.")

            user = self.session.query(User).filter_by(email=email).first()
            
            if user:
                if not user.avatar_url and id_info.get("picture"):
                    user.avatar_url = id_info.get("picture")
                    self.session.commit()
                return user
            
            new_user = User(
                username=username,
                email=email,
                first_name=id_info.get("given_name", "Unknown"),
                last_name=id_info.get("family_name", "User"),
                gender=gender,
                avatar_url=id_info.get("picture"),
                email_verified=id_info.get("email_verified", False)
            )  # type: ignore[no-untyped-call]
            new_user.set_password(os.urandom(24).hex())  # type: ignore[no-untyped-call]
            
            self.session.add(new_user)
            self.session.commit()
            self.session.refresh(new_user)
            return new_user

        except ValueError as e:
             raise AuthenticationError(f"Invalid Google Token: {str(e)}")
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f"Database error during Google OAuth: {str(e)}") from e