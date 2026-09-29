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


def test_forgot_password_replaces_existing_hash_with_new_hashed_password():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = SessionLocal()

    try:
        original = AuthService.register_user(
            db,
            email="reset@example.com",
            username="resetuser",
            password="oldpassword123",
        )
        old_hash = original.password_hash

        updated = AuthService.reset_password(db, "reset@example.com", "newpassword456")

        assert updated.email == original.email
        assert updated.password_hash != old_hash
        assert verify_password("newpassword456", updated.password_hash) is True
        assert verify_password("oldpassword123", updated.password_hash) is False
        assert AuthService.authenticate_user(db, "reset@example.com", "newpassword456") is not None
    finally:
        db.close()


def test_profile_and_preferences_can_be_updated_for_the_authenticated_user():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = SessionLocal()

    try:
        user = AuthService.register_user(
            db,
            email="profile@example.com",
            username="profileuser",
            password="Secret123!",
            full_name="Profile User",
        )

        updated = UserRepository(db).update_profile(
            user.email,
            {
                "username": "profileuser2",
                "full_name": "Updated User",
                "bio": "Loves vinyl",
                "profile_image": "https://example.com/avatar.png",
            },
        )

        assert updated.username == "profileuser2"
        assert updated.full_name == "Updated User"
        assert updated.bio == "Loves vinyl"
        assert updated.profile_image == "https://example.com/avatar.png"

        preferences = UserRepository(db).save_preferences(user.email, {
            "audio_quality": "lossless",
            "streaming_quality": "high",
            "autoplay": True,
            "crossfade": 6,
            "explicit_content": False,
            "theme": "midnight-violet",
            "dark_mode": True,
        })

        assert preferences.audio_quality == "lossless"
        assert preferences.dark_mode is True

        password_updated = UserRepository(db).change_password(user.email, "Secret123!", "NewSecret456!")
        assert password_updated is True
        assert AuthService.authenticate_user(db, user.email, "NewSecret456!") is not None
    finally:
        db.close()
