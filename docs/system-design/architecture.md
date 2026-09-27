# Architecture

The application follows a layered architecture:

- Presentation layer: React frontend
- Application layer: FastAPI endpoints and services
- Data access layer: SQLAlchemy repositories
- Persistence layer: PostgreSQL
- Storage layer: file system for audio and artwork assets

This separation supports maintainability, testability, and future scaling.
