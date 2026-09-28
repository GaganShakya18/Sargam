import uuid

from sqlalchemy import func

from models.user import User


class UserRepository:
    def __init__(self, database_session):
        self.db = database_session

    @staticmethod
    def normalize_email(email: str | None) -> str | None:
        if email is None:
            return None
        return email.strip().lower()

    @staticmethod
    def normalize_username(username: str | None) -> str | None:
        if username is None:
            return None
        return username.strip().lower()

    def get_by_email(self, email: str):
        normalized_email = self.normalize_email(email)
        if not normalized_email:
            return None
        return self.db.query(User).filter(func.lower(User.email) == normalized_email).first()

    def get_by_username(self, username: str):
        normalized_username = self.normalize_username(username)
        if not normalized_username:
            return None
        return self.db.query(User).filter(func.lower(User.username) == normalized_username).first()

    def create(self, payload: dict):
        raw_password = payload.get("password") or payload.get("password_hash")
        if not raw_password:
            raise ValueError("A password or password_hash is required")

        email = self.normalize_email(payload["email"])
        username = self.normalize_username(payload["username"])
        if not email or not username:
            raise ValueError("Email and username are required")

        full_name = payload.get("full_name")
        if full_name is not None:
            full_name = full_name.strip()
            if not full_name:
                full_name = None

        password_hash = payload.get("password_hash")
        if password_hash and password_hash.startswith("$2b$"):
            stored_hash = password_hash
        else:
            stored_hash = payload.get("password_hash") or raw_password
            if not stored_hash.startswith("$2b$"):
                from utils.hashing import hash_password

                stored_hash = hash_password(stored_hash)

        user = User(
            id=payload.get("id") or str(uuid.uuid4()),
            email=email,
            username=username,
            password_hash=stored_hash,
            full_name=full_name,
            is_active=payload.get("is_active", True),
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
