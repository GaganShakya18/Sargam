from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.auth import router as auth_router
from routes.songs import router as songs_router
from routes.playlists import router as playlists_router
from routes.search import router as search_router
from routes.users import router as users_router

app = FastAPI(
    title="MyMusicApp API",
    version="1.0.0",
    description="Music streaming backend for MyMusicApp",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(songs_router, prefix="/api/songs", tags=["songs"])
app.include_router(playlists_router, prefix="/api/playlists", tags=["playlists"])
app.include_router(search_router, prefix="/api/search", tags=["search"])
app.include_router(users_router, prefix="/api/users", tags=["users"])


@app.get("/")
def read_root():
    return {"message": "Welcome to MyMusicApp API"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
