from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_users():
    return {"items": []}


@router.get("/{user_id}")
def get_user(user_id: str):
    return {"user_id": user_id, "message": "User detail placeholder"}
