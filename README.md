# MyMusicApp

A full-stack music streaming application inspired by Spotify, built with FastAPI, PostgreSQL, and a React frontend.

## Project structure

- `backend/` - API server, business logic, models, routes, and tests
- `frontend/` - React app for the user interface
- `database/` - SQL schema, migrations, and ER docs
- `docs/` - architecture, use-cases, DSA, and design decisions
- `storage/` - music and artwork files
- `scripts/` - automation and maintenance utilities

## Tech stack

- Backend: FastAPI, SQLAlchemy, PostgreSQL
- Authentication: JWT
- Frontend: React + Vite
- Storage: local filesystem for media uploads

## Getting started

### 1. Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Copy the environment file and update it:

```bash
copy .env.example .env
```

Then run:

```bash
uvicorn main:app --reload
```

### 2. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

## Default admin credentials

- Email: admin@example.com
- Password: admin123

## Notes

This project is intended as a structured starter and can be extended with playlists, recommendations, search indexes, media streaming, and production deployment.
