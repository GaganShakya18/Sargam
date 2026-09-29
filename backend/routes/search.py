from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from config.database import get_db
from models.album import Album
from models.artist import Artist
from models.song import Song
from routes.songs import song_output

router = APIRouter()


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
