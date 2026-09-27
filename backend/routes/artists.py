from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_artists():
    return {"items": []}


@router.get("/{artist_id}")
def get_artist(artist_id: str):
    return {"artist_id": artist_id, "message": "Artist detail placeholder"}
