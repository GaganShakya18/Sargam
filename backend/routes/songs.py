import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from config.database import get_db
from config.settings import settings
from models.album import Album
from models.artist import Artist
from repositories.likes_repository import LikesRepository
from models.song import Song
from routes.users import get_authenticated_user

router = APIRouter()


def song_output(song, artist_name=None, album_title=None):
    return {
        "id": song.id,
        "title": song.title,
        "artist_name": artist_name,
        "album_title": album_title,
        "genre": song.genre,
        "duration_seconds": song.duration_seconds or 0,
        "audio_format": song.audio_format,
        "file_size": song.file_size,
        "cover_url": song.cover_url,
    }


def _catalog_query(database):
    return database.query(Song, Artist.name, Album.title).outerjoin(
        Artist, Song.artist_id == Artist.id
    ).outerjoin(Album, Song.album_id == Album.id).filter(Song.file_path.is_not(None))


@router.get("/")
def list_songs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    database: Session = Depends(get_db),
):
    query = _catalog_query(database)
    total = query.count()
    rows = query.order_by(Song.title).offset(offset).limit(limit).all()
    return {
        "items": [song_output(song, artist_name, album_title) for song, artist_name, album_title in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{song_id}")
def get_song(song_id: str, database: Session = Depends(get_db)):
    row = _catalog_query(database).filter(Song.id == song_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Song not found.")
    song, artist_name, album_title = row
    return song_output(song, artist_name, album_title)


@router.post("/{song_id}/like")
def like_song(
    song_id: str,
    database: Session = Depends(get_db),
    current_user=Depends(get_authenticated_user),
):
    song_exists = database.query(Song.id).filter(
        Song.id == song_id,
        Song.file_path.is_not(None),
    ).first()
    if song_exists is None:
        raise HTTPException(status_code=404, detail="Song not found.")
    created = LikesRepository(database).add(current_user.id, song_id)
    return {"liked": True, "created": created}


@router.delete("/{song_id}/like")
def unlike_song(
    song_id: str,
    database: Session = Depends(get_db),
    current_user=Depends(get_authenticated_user),
):
    song_exists = database.query(Song.id).filter(Song.id == song_id).first()
    if song_exists is None:
        raise HTTPException(status_code=404, detail="Song not found.")
    LikesRepository(database).remove(current_user.id, song_id)
    return {"liked": False}


@router.get("/{song_id}/like-status")
def get_song_like_status(
    song_id: str,
    database: Session = Depends(get_db),
    current_user=Depends(get_authenticated_user),
):
    song_exists = database.query(Song.id).filter(Song.id == song_id).first()
    if song_exists is None:
        raise HTTPException(status_code=404, detail="Song not found.")
    return {"liked": LikesRepository(database).is_liked(current_user.id, song_id)}


def _resolve_library_file(file_path):
    library_root = settings.music_library_path.expanduser().resolve()
    try:
        resolved_path = Path(file_path).resolve(strict=True)
        resolved_path.relative_to(library_root)
    except (OSError, RuntimeError, ValueError):
        raise HTTPException(status_code=404, detail="Song file is unavailable.") from None

    if not resolved_path.is_file() or resolved_path.suffix.lower() not in {
        ".mp3", ".flac", ".m4a", ".wav",
    }:
        raise HTTPException(status_code=404, detail="Song file is unavailable.")
    return resolved_path


def _file_chunks(file_path, start, length, chunk_size=64 * 1024):
    with file_path.open("rb") as audio_file:
        audio_file.seek(start)
        remaining = length
        while remaining:
            chunk = audio_file.read(min(chunk_size, remaining))
            if not chunk:
                break
            remaining -= len(chunk)
            yield chunk


@router.get("/{song_id}/stream")
def stream_song(song_id: str, request: Request, database: Session = Depends(get_db)):
    song = database.query(Song).filter(
        Song.id == song_id,
        Song.file_path.is_not(None),
    ).first()
    if song is None:
        raise HTTPException(status_code=404, detail="Song not found.")

    file_path = _resolve_library_file(song.file_path)
    file_size = file_path.stat().st_size
    start = 0
    end = file_size - 1
    status_code = 200
    headers = {"Accept-Ranges": "bytes"}
    range_header = request.headers.get("range")

    if range_header:
        match = re.fullmatch(r"bytes=(\d*)-(\d*)", range_header.strip())
        if match is None or file_size == 0:
            return Response(status_code=416, headers={"Content-Range": f"bytes */{file_size}"})
        range_start, range_end = match.groups()
        if range_start:
            start = int(range_start)
            end = int(range_end) if range_end else file_size - 1
        elif range_end:
            suffix_length = int(range_end)
            if suffix_length == 0:
                return Response(status_code=416, headers={"Content-Range": f"bytes */{file_size}"})
            start = max(0, file_size - suffix_length)
        if start >= file_size or end < start:
            return Response(status_code=416, headers={"Content-Range": f"bytes */{file_size}"})
        end = min(end, file_size - 1)
        status_code = 206
        headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"

    length = max(0, end - start + 1)
    headers["Content-Length"] = str(length)
    media_type = {
        ".mp3": "audio/mpeg",
        ".flac": "audio/flac",
        ".m4a": "audio/mp4",
        ".wav": "audio/wav",
    }[file_path.suffix.lower()]
    return StreamingResponse(
        _file_chunks(file_path, start, length),
        status_code=status_code,
        media_type=media_type,
        headers=headers,
    )


@router.post("/")
def create_song():
    return {"message": "Create song placeholder"}
