import sys
import os
from pathlib import Path


project_root = Path(__file__).resolve().parent.parent
backend_root = project_root / "backend"
os.chdir(backend_root)
sys.path.insert(0, str(backend_root))

from config.database import Base, SessionLocal, engine, ensure_song_library_columns
from config.settings import settings
from models import Album, Artist, Song, User  # noqa: F401
from services.library_scanner import scan_music_library


def main():
    Base.metadata.create_all(bind=engine)
    ensure_song_library_columns()
    database = SessionLocal()
    try:
        result = scan_music_library(database)
    except FileNotFoundError as error:
        raise SystemExit(str(error)) from None
    finally:
        database.close()

    print(
        f"Scanned {settings.music_library_path}: {result['found']} supported files, "
        f"{result['added']} added, {result['updated']} updated, {result['skipped']} skipped."
    )


if __name__ == "__main__":
    main()
