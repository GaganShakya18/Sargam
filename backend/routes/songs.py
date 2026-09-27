from fastapi import APIRouter, Query

router = APIRouter()


@router.get("/")
def list_songs(limit: int = Query(20, ge=1), offset: int = Query(0, ge=0)):
    return {"items": [], "limit": limit, "offset": offset}


@router.get("/{song_id}")
def get_song(song_id: str):
    return {"song_id": song_id, "message": "Song detail placeholder"}


@router.post("/")
def create_song():
    return {"message": "Create song placeholder"}
