from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_albums():
    return {"items": []}


@router.get("/{album_id}")
def get_album(album_id: str):
    return {"album_id": album_id, "message": "Album detail placeholder"}
