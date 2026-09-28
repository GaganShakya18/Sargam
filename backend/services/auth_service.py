from repositories.user_repository import UserRepository
from utils.hashing import hash_password, verify_password
from utils.jwt import create_access_token


class AuthService:
    @staticmethod
    def register_user(db, email: str, username: str, password: str, full_name: str | None = None):
        repo = UserRepository(db)
        if repo.get_by_email(email):
            raise ValueError("Email already registered")
        if repo.get_by_username(username):
            raise ValueError("Username already taken")

        return repo.create({
            "email": email,
            "username": username,
            "full_name": full_name,
            "password": password,
        })

    @staticmethod
    def authenticate_user(db, email: str, password: str):
        repo = UserRepository(db)
        user = repo.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    @staticmethod
    def create_token_for_user(user_email: str):
        return create_access_token({"sub": user_email})
