from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

from config.settings import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_song_library_columns():
    inspector = inspect(engine)
    if not inspector.has_table("songs"):
        return

    columns = {column["name"] for column in inspector.get_columns("songs")}
    additions = {
        "file_path": "TEXT",
        "audio_format": "VARCHAR(16)",
        "file_size": "BIGINT",
    }
    with engine.begin() as connection:
        for column_name, column_type in additions.items():
            if column_name not in columns:
                connection.execute(text(
                    f"ALTER TABLE songs ADD COLUMN {column_name} {column_type}"
                ))
        connection.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_songs_file_path "
            "ON songs (file_path)"
        ))
