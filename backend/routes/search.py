from fastapi import APIRouter, Query

router = APIRouter()


@router.get("/")
def search_music(q: str = Query(..., min_length=1)):
    return {"query": q, "results": []}
