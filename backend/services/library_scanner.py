import uuid
from pathlib import Path

from sqlalchemy import func

from config.settings import settings
from models.album import Album
from models.artist import Artist
from models.song import Song


SUPPORTED_FORMATS = {".mp3", ".flac", ".m4a", ".wav"}


def _tag_value(tags, key):
    value = tags.get(key) if tags else None
    if isinstance(value, (list, tuple)):
        value = value[0] if value else None
    return str(value).strip() if value is not None else ""


def _stable_id(value):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, value.casefold()))


def read_audio_metadata(path):
    from mutagen import File, MutagenError

    try:
        media = File(path, easy=True)
        if media is None or media.info is None:
            return None
        tags = media.tags or {}
        duration = float(media.info.length)
    except (MutagenError, OSError, ValueError, TypeError):
        return None
    return tags, duration


def scan_music_library(database):
    library_root = settings.music_library_path.expanduser().resolve()
    if not library_root.is_dir():
        raise FileNotFoundError("Configured music library folder does not exist.")

    stats = {"found": 0, "added": 0, "updated": 0, "skipped": 0}
    files = []
    for path in library_root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_FORMATS:
            continue
        try:
            resolved_path = path.resolve(strict=True)
            resolved_path.relative_to(library_root)
        except (OSError, RuntimeError, ValueError):
            continue
        files.append(resolved_path)
    files.sort()
    discovered_paths = {str(path) for path in files}

    for path in files:
        stats["found"] += 1
        try:
            metadata = read_audio_metadata(path)
            if metadata is None:
                stats["skipped"] += 1
                continue

            tags, duration_seconds = metadata
            title = _tag_value(tags, "title") or path.stem
            artist_name = _tag_value(tags, "artist") or "Unknown Artist"
            album_title = _tag_value(tags, "album")
            genre = _tag_value(tags, "genre") or None
            duration = max(0, int(round(duration_seconds)))
            file_size = path.stat().st_size
        except (OSError, ValueError, TypeError, AttributeError):
            stats["skipped"] += 1
            continue

        artist = database.query(Artist).filter(
            func.lower(Artist.name) == artist_name.casefold()
        ).first()
        if artist is None:
            artist = Artist(id=_stable_id(f"artist:{artist_name}"), name=artist_name)
            database.add(artist)
            database.flush()

        album = None
        if album_title:
            album = database.query(Album).filter(
                Album.artist_id == artist.id,
                func.lower(Album.title) == album_title.casefold(),
            ).first()
            if album is None:
                album = Album(
                    id=_stable_id(f"album:{artist.id}:{album_title}"),
                    title=album_title,
                    artist_id=artist.id,
                )
                database.add(album)
                database.flush()

        file_path = str(path)
        song = database.query(Song).filter(Song.file_path == file_path).first()
        if song is None:
            song = database.query(Song).filter(
                Song.id == _stable_id(f"song:{file_path}")
            ).first()
        is_new = song is None
        if is_new:
            song = Song(id=_stable_id(f"song:{file_path}"), file_path=file_path)
            database.add(song)
        else:
            song.file_path = file_path

        song.title = title
        song.artist_id = artist.id
        song.album_id = album.id if album else None
        song.genre = genre
        song.duration_seconds = duration
        song.audio_format = path.suffix[1:].lower()
        song.file_size = file_size
        stats["added" if is_new else "updated"] += 1

    for song in database.query(Song).filter(Song.file_path.is_not(None)).all():
        if song.file_path not in discovered_paths:
            song.file_path = None

    database.commit()
    return stats