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
