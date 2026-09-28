from unittest.mock import MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.database import Base
from repositories.user_repository import UserRepository
from services.auth_service import AuthService
from utils.hashing import verify_password


def test_user_repository_create_stores_hashed_password():
    db = MagicMock()
    repo = UserRepository(db)

    user = repo.create({
        "email": "alice@example.com",
        "username": "alice",
        "full_name": "Alice Smith",
        "password": "secret123",
    })

    db.add.assert_called_once()
    db.commit.assert_called_once()
    assert user.email == "alice@example.com"
    assert user.username == "alice"
    assert user.password_hash != "secret123"
    assert verify_password("secret123", user.password_hash) is True


def test_user_registration_and_login_persist_normalized_user_data():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = SessionLocal()

    try:
        user = AuthService.register_user(
            db,
            email="  Alice@Example.com ",
            username=" AliceUser ",
            password="Secret123!",
            full_name="Alice Smith",
        )

        assert user.email == "alice@example.com"
        assert user.username == "aliceuser"
        assert user.full_name == "Alice Smith"
        assert verify_password("Secret123!", user.password_hash) is True

        authenticated = AuthService.authenticate_user(db, "alice@example.com", "Secret123!")
        assert authenticated is not None
        assert authenticated.id == user.id
    finally:
        db.close()
