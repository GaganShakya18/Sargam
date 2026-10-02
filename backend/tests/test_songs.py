import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from config.database import Base, get_db
from config.settings import settings
from models import Album, Artist, Song
from routes.recommendations import router as recommendations_router
from routes.search import router as search_router
from routes.songs import router as songs_router
from routes.users import router as users_router
from services.auth_service import AuthService
from services import library_scanner
from utils.jwt import create_access_token


@pytest.fixture
def music_client(tmp_path, monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    test_sessions = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    monkeypatch.setattr(settings, "music_library_path", tmp_path)

    app = FastAPI()
    app.include_router(songs_router, prefix="/api/songs")
    app.include_router(search_router, prefix="/api/search")
    from routes.recommendations import router as test_recommendations_router
    from routes.users import router as test_users_router

    app.include_router(test_users_router, prefix="/api/users")
    app.include_router(test_recommendations_router, prefix="/api/recommendations")
    assert any(route.path == "/api/users/me/liked-songs" for route in app.routes)

    def override_database():
        database = test_sessions()
        try:
            yield database
        finally:
            database.close()

    app.dependency_overrides[get_db] = override_database
    with TestClient(app) as client:
        yield client, test_sessions
    engine.dispose()


def test_scan_is_idempotent_and_searchable(music_client, tmp_path, monkeypatch):
    client, test_sessions = music_client
    track = tmp_path / "Hindi" / "Blue Train.mp3"
    track.parent.mkdir()
    track.write_bytes(b"audio bytes")
    monkeypatch.setattr(
        library_scanner,
        "read_audio_metadata",
        lambda path: ({"title": ["Blue Train"], "artist": ["John Coltrane"], "album": ["Blue Train"], "genre": ["Jazz"]}, 141.2),
    )

    database = test_sessions()
    try:
        first_scan = library_scanner.scan_music_library(database)
        second_scan = library_scanner.scan_music_library(database)
        assert first_scan == {"found": 1, "added": 1, "updated": 0, "skipped": 0}
        assert second_scan == {"found": 1, "added": 0, "updated": 1, "skipped": 0}
        assert database.query(Song).count() == 1
    finally:
        database.close()

    response = client.get("/api/search/", params={"q": "Coltrane"})
    assert response.status_code == 200
    assert response.json()["results"][0]["title"] == "Blue Train"
    assert response.json()["results"][0]["duration_seconds"] == 141
    streamed = client.get(f"/api/songs/{response.json()['results'][0]['id']}/stream")
    assert streamed.status_code == 200
    assert streamed.content == b"audio bytes"


def test_catalog_refresh_hides_removed_files_and_restores_readded_files(music_client, tmp_path, monkeypatch):
    client, test_sessions = music_client
    track = tmp_path / "Dynamic Track.mp3"
    track.write_bytes(b"first audio bytes")
    monkeypatch.setattr(
        library_scanner,
        "read_audio_metadata",
        lambda path: ({"title": ["Dynamic Track"], "artist": ["Test Artist"]}, 180),
    )

    database = test_sessions()
    try:
        library_scanner.scan_music_library(database)
        song_id = database.query(Song).one().id
    finally:
        database.close()

    track.unlink()
    removed_response = client.get("/api/songs/")
    assert removed_response.status_code == 200
    assert removed_response.json()["items"] == []
    assert client.get(f"/api/songs/{song_id}/stream").status_code == 404

    track.write_bytes(b"replacement audio bytes")
    restored_response = client.get("/api/songs/")
    assert restored_response.status_code == 200
    assert [song["id"] for song in restored_response.json()["items"]] == [song_id]
    assert client.get(f"/api/songs/{song_id}/stream").content == b"replacement audio bytes"


def test_stream_supports_ranges_and_rejects_outside_paths(music_client, tmp_path):
    client, test_sessions = music_client
    safe_file = tmp_path / "safe.mp3"
    safe_file.write_bytes(b"0123456789")
    outside_file = tmp_path.parent / "private.mp3"
    outside_file.write_bytes(b"private")
    database = test_sessions()
    try:
        artist = Artist(id="artist-1", name="Test Artist")
        safe_song = Song(
            id="song-safe", title="Safe", artist_id=artist.id,
            file_path=str(safe_file), audio_format="mp3", file_size=10,
        )
        outside_song = Song(
            id="song-outside", title="Outside", artist_id=artist.id,
            file_path=str(outside_file), audio_format="mp3", file_size=7,
        )
        database.add_all([artist, safe_song, outside_song])
        database.commit()
    finally:
        database.close()

    ranged = client.get("/api/songs/song-safe/stream", headers={"Range": "bytes=2-5"})
    assert ranged.status_code == 206
    assert ranged.content == b"2345"
    assert ranged.headers["content-range"] == "bytes 2-5/10"

    outside = client.get("/api/songs/song-outside/stream")
    assert outside.status_code == 404


def test_empty_library_scans_without_creating_records(music_client):
    _, test_sessions = music_client
    database = test_sessions()
    try:
        result = library_scanner.scan_music_library(database)
        assert result == {"found": 0, "added": 0, "updated": 0, "skipped": 0}
        assert database.query(Song).count() == 0
    finally:
        database.close()


def test_suggestions_rank_catalog_matches_and_return_song_artist_album_types(music_client, tmp_path):
    client, test_sessions = music_client
    database = test_sessions()
    try:
        artist = Artist(id="artist-mahiya", name="Mahiya Artist")
        album = Album(id="album-mahiya", title="Mahiya Album", artist_id=artist.id)
        rows = [
            Song(
                id="song-prefix",
                title="Mahiya - PagalNew",
                artist_id=artist.id,
                album_id=album.id,
                file_path=str(tmp_path / "prefix.mp3"),
            ),
            Song(
                id="song-partial",
                title="A Song About Mahiya",
                artist_id=artist.id,
                album_id=album.id,
                file_path=str(tmp_path / "partial.mp3"),
            ),
        ]
        database.add_all([artist, album, *rows])
        database.commit()
    finally:
        database.close()

    response = client.get("/api/search/suggestions", params={"q": "mahi"})
    assert response.status_code == 200
    suggestions = response.json()["suggestions"]
    assert suggestions[0] == {
        "type": "song",
        "id": "song-prefix",
        "title": "Mahiya - PagalNew",
        "artist": "Mahiya Artist",
        "album": "Mahiya Album",
    }
    assert {item["type"] for item in suggestions} == {"song", "artist", "album"}
    assert len(suggestions) <= 8


def test_suggestions_require_two_characters_and_limit_results(music_client):
    client, _ = music_client
    short_query = client.get("/api/search/suggestions", params={"q": "m"})
    assert short_query.status_code == 422

    bounded = client.get("/api/search/suggestions", params={"q": "mahi", "limit": 2})
    assert bounded.status_code == 200
    assert bounded.json()["suggestions"] == []


def test_likes_are_persistent_user_scoped_and_drive_recommendations(music_client, tmp_path):
    client, test_sessions = music_client
    client.app.include_router(users_router, prefix="/api/users")
    client.app.include_router(recommendations_router, prefix="/api/recommendations")
    database = test_sessions()
    first_user = AuthService.register_user(
        database,
        email="first@example.com",
        username="firstuser",
        password="Secret123!",
    )
    second_user = AuthService.register_user(
        database,
        email="second@example.com",
        username="seconduser",
        password="Secret123!",
    )
    artist = Artist(id="library-artist", name="Library Artist")
    seed = Song(
        id="liked-seed", title="Seed Track", artist_id=artist.id, genre="Jazz",
        file_path=str(tmp_path / "seed.mp3"),
    )
    recommendation = Song(
        id="recommended-track", title="Related Track", artist_id=artist.id, genre="Jazz",
        file_path=str(tmp_path / "related.mp3"),
    )
    database.add_all([artist, seed, recommendation])
    database.commit()
    first_token = create_access_token({"sub": first_user.email})
    second_token = create_access_token({"sub": second_user.email})
    database.close()
    first_headers = {"Authorization": f"Bearer {first_token}"}
    second_headers = {"Authorization": f"Bearer {second_token}"}

    liked = client.post("/api/songs/liked-seed/like", headers=first_headers)
    assert liked.status_code == 200
    assert liked.json()["liked"] is True
    duplicate = client.post("/api/songs/liked-seed/like", headers=first_headers)
    assert duplicate.json()["created"] is False
    first_likes = client.get("/api/users/me/liked-songs", headers=first_headers)
    second_likes = client.get("/api/users/me/liked-songs", headers=second_headers)
    assert first_likes.status_code == 200, (
        f"{first_likes.request.url}: {first_likes.text}; "
        f"routes={[route.path for route in client.app.routes]}"
    )
    assert second_likes.status_code == 200, second_likes.text
    assert first_likes.json()["total"] == 1
    assert second_likes.json()["total"] == 0

    history = client.post(
        "/api/users/me/listening-history",
        json={"song_id": "liked-seed"},
        headers=first_headers,
    )
    assert history.json()["recorded"] is True
    assert client.get("/api/users/me/listening-history", headers=first_headers).json()["items"][0]["id"] == "liked-seed"

    recommendations = client.get("/api/recommendations/", headers=first_headers)
    assert [song["id"] for song in recommendations.json()["recommendations"]] == ["recommended-track"]
    assert client.get("/api/recommendations/", headers=second_headers).json()["recommendations"] == []

    unliked = client.delete("/api/songs/liked-seed/like", headers=first_headers)
    assert unliked.status_code == 200
    assert client.get("/api/users/me/liked-songs", headers=first_headers).json()["items"] == []
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from config.database import Base, get_db
from config.settings import settings
from models import Artist, Song
from routes.search import router as search_router
from routes.songs import router as songs_router
from services import library_scanner


@pytest.fixture
def music_client(tmp_path, monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    test_sessions = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    monkeypatch.setattr(settings, "music_library_path", tmp_path)

    app = FastAPI()
    app.include_router(songs_router, prefix="/api/songs")
    app.include_router(search_router, prefix="/api/search")

    def override_database():
        database = test_sessions()
        try:
            yield database
        finally:
            database.close()

    app.dependency_overrides[get_db] = override_database
    with TestClient(app) as client:
        yield client, test_sessions
    engine.dispose()


def test_scan_is_idempotent_and_searchable(music_client, tmp_path, monkeypatch):
    client, test_sessions = music_client
    track = tmp_path / "Hindi" / "Blue Train.mp3"
    track.parent.mkdir()
    track.write_bytes(b"audio bytes")
    monkeypatch.setattr(
        library_scanner,
        "read_audio_metadata",
        lambda path: (
            {
                "title": ["Blue Train"],
                "artist": ["John Coltrane"],
                "album": ["Blue Train"],
                "genre": ["Jazz"],
            },
            141.2,
        ),
    )

    database = test_sessions()
    try:
        first_scan = library_scanner.scan_music_library(database)
        second_scan = library_scanner.scan_music_library(database)
        assert first_scan == {"found": 1, "added": 1, "updated": 0, "skipped": 0}
        assert second_scan == {"found": 1, "added": 0, "updated": 1, "skipped": 0}
        assert database.query(Song).count() == 1
    finally:
        database.close()

    response = client.get("/api/search/", params={"q": "Coltrane"})
    assert response.status_code == 200
    assert response.json()["results"][0]["title"] == "Blue Train"
    assert response.json()["results"][0]["duration_seconds"] == 141


def test_stream_supports_ranges_and_rejects_outside_paths(music_client, tmp_path):
    client, test_sessions = music_client
    safe_file = tmp_path / "safe.mp3"
    safe_file.write_bytes(b"0123456789")
    outside_file = tmp_path.parent / "private.mp3"
    outside_file.write_bytes(b"private")
    database = test_sessions()
    try:
        artist = Artist(id="artist-1", name="Test Artist")
        safe_song = Song(
            id="song-safe",
            title="Safe",
            artist_id=artist.id,
            file_path=str(safe_file),
            audio_format="mp3",
            file_size=10,
        )
        outside_song = Song(
            id="song-outside",
            title="Outside",
            artist_id=artist.id,
            file_path=str(outside_file),
            audio_format="mp3",
            file_size=7,
        )
        database.add_all([artist, safe_song, outside_song])
        database.commit()
    finally:
        database.close()

    ranged = client.get("/api/songs/song-safe/stream", headers={"Range": "bytes=2-5"})
    assert ranged.status_code == 206
    assert ranged.content == b"2345"
    assert ranged.headers["content-range"] == "bytes 2-5/10"

    outside = client.get("/api/songs/song-outside/stream")
    assert outside.status_code == 404


def test_empty_library_scans_without_creating_records(music_client):
    _, test_sessions = music_client
    database = test_sessions()
    try:
        result = library_scanner.scan_music_library(database)
        assert result == {"found": 0, "added": 0, "updated": 0, "skipped": 0}
        assert database.query(Song).count() == 0
    finally:
        database.close()
