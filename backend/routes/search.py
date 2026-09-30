from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from config.database import get_db
from models.album import Album
from models.artist import Artist
from models.song import Song
from routes.songs import song_output

router = APIRouter()


@router.get("/suggestions")
def search_suggestions(
    q: str = Query(..., min_length=2, max_length=100),
    limit: int = Query(8, ge=1, le=10),
    database: Session = Depends(get_db),
):
    query = q.strip()
    if len(query) < 2:
        return {"query": query, "suggestions": []}

    normalized_query = query.lower()
    prefix = f"{query}%"
    partial = f"%{query}%"
    song_rank = case(
        (func.lower(Song.title) == normalized_query, 0),
        (Song.title.ilike(prefix), 1),
        (Artist.name.ilike(prefix), 2),
        (Album.title.ilike(prefix), 3),
        (Song.title.ilike(partial), 4),
        (Artist.name.ilike(partial), 5),
        (Album.title.ilike(partial), 6),
        (Song.genre.ilike(partial), 7),
        else_=8,
    )
    song_rows = database.query(Song, Artist.name, Album.title, song_rank.label("rank")).outerjoin(
        Artist, Song.artist_id == Artist.id
    ).outerjoin(Album, Song.album_id == Album.id).filter(
        Song.file_path.is_not(None),
        (Song.title.ilike(partial)
         | Artist.name.ilike(partial)
         | Album.title.ilike(partial)
         | Song.genre.ilike(partial)),
    ).order_by(song_rank, Song.title).limit(limit).all()

    artist_rank = case(
        (Artist.name.ilike(prefix), 2),
        else_=5,
    )
    artist_rows = database.query(Artist, artist_rank.label("rank")).join(
        Song, Song.artist_id == Artist.id
    ).filter(
        Song.file_path.is_not(None),
        Artist.name.ilike(partial),
    ).distinct().order_by(artist_rank, Artist.name).limit(limit).all()

    album_rank = case(
        (Album.title.ilike(prefix), 3),
        else_=6,
    )
    album_rows = database.query(Album, Artist.name, album_rank.label("rank")).join(
        Song, Song.album_id == Album.id
    ).join(Artist, Album.artist_id == Artist.id).filter(
        Song.file_path.is_not(None),
        Album.title.ilike(partial),
    ).distinct().order_by(album_rank, Album.title).limit(limit).all()

    ranked_suggestions = []
    ranked_suggestions.extend(
        (rank, 0, {
            "type": "song",
            "id": song.id,
            "title": song.title,
            "artist": artist_name,
            "album": album_title,
        })
        for song, artist_name, album_title, rank in song_rows
    )
    ranked_suggestions.extend(
        (rank, 1, {"type": "artist", "id": artist.id, "name": artist.name})
        for artist, rank in artist_rows
    )
    ranked_suggestions.extend(
        (rank, 2, {"type": "album", "id": album.id, "name": album.title, "artist": artist_name})
        for album, artist_name, rank in album_rows
    )
    ranked_suggestions.sort(key=lambda item: (item[0], item[1]))

    return {
        "query": query,
        "suggestions": [item[2] for item in ranked_suggestions[:limit]],
    }


@router.get("/")
def search_music(q: str = Query(..., min_length=1), database: Session = Depends(get_db)):
    pattern = f"%{q.strip()}%"
    rows = database.query(Song, Artist.name, Album.title).outerjoin(
        Artist, Song.artist_id == Artist.id
    ).outerjoin(Album, Song.album_id == Album.id).filter(
        Song.file_path.is_not(None),
        (Song.title.ilike(pattern)
         | Artist.name.ilike(pattern)
         | Album.title.ilike(pattern)
         | Song.genre.ilike(pattern)),
    ).order_by(Song.title).limit(100).all()
    return {
        "query": q,
        "results": [song_output(song, artist_name, album_title) for song, artist_name, album_title in rows],
    }
