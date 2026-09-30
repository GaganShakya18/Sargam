from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from config.database import Base, get_db
from repositories.user_repository import UserRepository
from routes.users import router as users_router
from services.auth_service import AuthService
from utils.jwt import create_access_token
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


def test_search_history_routes_respect_privacy_and_clear_history():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    test_sessions = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    database = test_sessions()
    user = AuthService.register_user(
        database,
        email="history@example.com",
        username="historyuser",
        password="Secret123!",
    )
    user_email = user.email
    database.close()

    app = FastAPI()
    app.include_router(users_router, prefix="/api/users")

    def override_database():
        request_database = test_sessions()
        try:
            yield request_database
        finally:
            request_database.close()

    app.dependency_overrides[get_db] = override_database
    headers = {"Authorization": f"Bearer {create_access_token({'sub': user_email})}"}

    with TestClient(app) as client:
        recorded = client.post(
            "/api/users/me/search-history",
            json={"query": "  mahiya  "},
            headers=headers,
        )
        assert recorded.status_code == 200
        assert recorded.json() == {"saved": True}
        duplicate = client.post(
            "/api/users/me/search-history",
            json={"query": "MAHIYA"},
            headers=headers,
        )
        assert duplicate.status_code == 200

        history = client.get("/api/users/me/search-history", headers=headers)
        assert [item["query"] for item in history.json()["items"]] == ["MAHIYA"]

        disabled = client.patch(
            "/api/users/me/privacy",
            json={"search_history_enabled": False},
            headers=headers,
        )
        assert disabled.status_code == 200
        not_recorded = client.post(
            "/api/users/me/search-history",
            json={"query": "another song"},
            headers=headers,
        )
        assert not_recorded.json() == {"saved": False}
        assert client.get("/api/users/me/search-history", headers=headers).json() == {
            "enabled": False,
            "items": [],
        }

        client.patch(
            "/api/users/me/privacy",
            json={"search_history_enabled": True},
            headers=headers,
        )
        cleared = client.delete("/api/users/me/search-history", headers=headers)
        assert cleared.status_code == 200
        assert client.get("/api/users/me/search-history", headers=headers).json()["items"] == []

    engine.dispose()
