import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from config.database import Base, get_db
from models import Playlist, Song
from routes.playlists import router as playlists_router
from services.auth_service import AuthService
from utils.jwt import create_access_token


@pytest.fixture
def playlist_client(tmp_path):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    test_sessions = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    app = FastAPI()
    app.include_router(playlists_router, prefix="/api/playlists")

    def override_database():
        database = test_sessions()
        try:
            yield database
        finally:
            database.close()

    app.dependency_overrides[get_db] = override_database
    with TestClient(app) as client:
        database = test_sessions()
        owner = AuthService.register_user(
            database, "owner@example.com", "owner", "Secret123!"
        )
        other_user = AuthService.register_user(
            database, "other@example.com", "other", "Secret123!"
        )
        database.add(Song(
            id="song-1",
            title="Test Song",
            artist_id="artist-1",
            file_path=str(tmp_path / "song.mp3"),
        ))
        database.commit()
        users = {
            "owner": {"Authorization": f"Bearer {create_access_token({'sub': owner.email})}"},
            "other": {"Authorization": f"Bearer {create_access_token({'sub': other_user.email})}"},
            "other_id": other_user.id,
        }
        database.close()
        yield client, test_sessions, users
    engine.dispose()


def test_playlist_creation_and_song_membership_are_persistent_and_owner_scoped(playlist_client):
    client, test_sessions, users = playlist_client
    assert client.post("/api/playlists/", json={"name": "Anonymous"}).status_code == 403
    created = client.post(
        "/api/playlists/",
        json={"name": "Workout", "description": "Training mix", "user_id": users["other_id"]},
        headers=users["owner"],
    )
    assert created.status_code == 201
    playlist = created.json()
    assert playlist["name"] == "Workout"
    assert playlist["description"] == "Training mix"

    owner_playlists = client.get("/api/playlists/", headers=users["owner"])
    other_playlists = client.get("/api/playlists/", headers=users["other"])
    assert [item["id"] for item in owner_playlists.json()["items"]] == [playlist["id"]]
    assert other_playlists.json()["items"] == []

    add_path = f"/api/playlists/{playlist['id']}/songs"
    added = client.post(add_path, json={"song_id": "song-1"}, headers=users["owner"])
    duplicate = client.post(add_path, json={"song_id": "song-1"}, headers=users["owner"])
    denied = client.post(add_path, json={"song_id": "song-1"}, headers=users["other"])
    assert added.status_code == 200
    assert added.json() == {"added": True}
    assert duplicate.json() == {"added": False}
    assert denied.status_code == 404

    database = test_sessions()
    try:
        membership = database.execute(text(
            "SELECT playlist_id, song_id FROM playlist_songs"
        )).one()
        assert tuple(membership) == (playlist["id"], "song-1")
        assert database.query(Playlist).filter_by(user_id=users["other_id"]).count() == 0
    finally:
        database.close()
