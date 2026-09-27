from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.post("/register")
def register_user():
    return {"message": "Register endpoint placeholder"}


@router.post("/login")
def login_user():
    return {"message": "Login endpoint placeholder"}


@router.get("/me")
def get_current_user():
    return {"message": "Current user endpoint placeholder"}
