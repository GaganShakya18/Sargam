from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from config.database import Base, engine, ensure_song_library_columns
from config.settings import settings
from models import *  # noqa: F401,F403
from routes.auth import router as auth_router
from routes.songs import router as songs_router
from routes.playlists import router as playlists_router
from routes.search import router as search_router
from routes.recommendations import router as recommendations_router
from routes.users import router as users_router

if engine.dialect.name == "sqlite":
    inspector = inspect(engine)
    if inspector.has_table("users"):
        user_columns = {column["name"] for column in inspector.get_columns("users")}
        missing_user_columns = {
            "bio": "VARCHAR",
            "profile_image": "VARCHAR",
            "account_type": "VARCHAR DEFAULT 'Free'",
        }
        with engine.begin() as connection:
            for column_name, definition in missing_user_columns.items():
                if column_name not in user_columns:
                    connection.execute(text(
                        f"ALTER TABLE users ADD COLUMN {column_name} {definition}"
                    ))

Base.metadata.create_all(bind=engine)
ensure_song_library_columns()

app = FastAPI(
    title="MyMusicApp API",
    version="1.0.0",
    description="Music streaming backend for MyMusicApp",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_origin_regex=settings.cors_allowed_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(songs_router, prefix="/api/songs", tags=["songs"])
app.include_router(playlists_router, prefix="/api/playlists", tags=["playlists"])
app.include_router(search_router, prefix="/api/search", tags=["search"])
app.include_router(recommendations_router, prefix="/api/recommendations", tags=["recommendations"])
app.include_router(users_router, prefix="/api/users", tags=["users"])


@app.get("/")
def read_root():
    return {"message": "Welcome to MyMusicApp API"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
