from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config.database import get_db
from repositories.user_repository import UserRepository
from schemas.user_schema import PasswordChangeRequest, PasswordResetRequest, UserCreate, UserLogin, UserOut
from services.auth_service import AuthService
from utils.jwt import decode_access_token

router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=UserOut)
def register_user(payload: UserCreate, db=Depends(get_db)):
    try:
        user = AuthService.register_user(
            db,
            email=payload.email,
            username=payload.username,
            password=payload.password,
            full_name=payload.full_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return user


@router.post("/login")
def login_user(payload: UserLogin, db=Depends(get_db)):
    user = AuthService.authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = AuthService.create_token_for_user(user.email)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
        },
    }


@router.post("/forgot-password")
def forgot_password(payload: PasswordResetRequest, db=Depends(get_db)):
    try:
        AuthService.reset_password(db, payload.email, payload.new_password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return {"message": "Password updated successfully. Please log in with your new password."}


@router.post("/change-password")
def change_password(
    payload: PasswordChangeRequest,
    db=Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    decoded = decode_access_token(token)
    if not decoded or not decoded.get("sub"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user = UserRepository(db).get_by_email(decoded["sub"])
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    try:
        UserRepository(db).change_password(user.email, payload.current_password, payload.new_password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return {"message": "Password updated successfully."}


@router.post("/logout")
def logout_user(
    db=Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    decoded = decode_access_token(token)
    if not decoded or not decoded.get("sub"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    UserRepository(db).get_by_email(decoded["sub"])
    return {"message": "Logged out successfully."}


@router.get("/me", response_model=UserOut)
def get_current_user(
    request: Request,
    db=Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user = UserRepository(db).get_by_email(payload["sub"])
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user
