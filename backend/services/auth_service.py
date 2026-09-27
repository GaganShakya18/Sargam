from utils.hashing import hash_password, verify_password
from utils.jwt import create_access_token


class AuthService:
    @staticmethod
    def register_user(email: str, username: str, password: str):
        return {
            "email": email,
            "username": username,
            "password_hash": hash_password(password),
        }

    @staticmethod
    def authenticate_user(email: str, password: str, stored_password: str):
        return verify_password(password, stored_password)

    @staticmethod
    def create_token_for_user(user_email: str):
        return create_access_token({"sub": user_email})
