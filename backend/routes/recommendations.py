from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from config.database import get_db
from repositories.user_repository import UserRepository
from routes.users import get_authenticated_user
from services.recommendation_service import RecommendationService


router = APIRouter()


@router.get("/")
def get_recommendations(
    limit: int = Query(10, ge=1, le=30),
    database: Session = Depends(get_db),
    current_user=Depends(get_authenticated_user),
):
    privacy = UserRepository(database).get_privacy(current_user.email)
    recommendations = RecommendationService(database).get_recommendations(
        current_user.id,
        limit=limit,
        include_history=privacy.listening_history_enabled,
    )
    return {"recommendations": recommendations}