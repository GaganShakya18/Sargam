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

### Music library

The backend reads audio files from `MUSIC_LIBRARY_PATH` (default:
`C:\Users\Gagan\Downloads\music`). Override it in `backend/.env` when needed.
Supported formats are MP3, FLAC, M4A, and WAV. Audio stays on disk; the configured
SQLAlchemy database stores the catalog metadata and file references.

Install backend dependencies once from the project root:

```powershell
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

Scan or rescan the library after adding files:

```powershell
npm run scan:music
```

The Android/React app loads songs through `GET /api/songs/`, searches through the
existing `GET /api/search/?q=...` endpoint, and plays `GET /api/songs/{song_id}/stream`.
The stream endpoint confines resolved paths to `MUSIC_LIBRARY_PATH` and supports
HTTP byte ranges for seeking. Set `VITE_API_BASE_URL` in `frontend/.env` to the
FastAPI host reachable by the device; Android phones must use the laptop's
LAN address, not `localhost`.

### One-command development

From the project root, run:

```powershell
npm run dev
```

This starts the existing FastAPI `--reload` process and Vite dev server. Configure
`DATABASE_URL` in `backend/.env` for PostgreSQL before expecting the catalog to be
stored in PostgreSQL. The current local environment is configured for SQLite and
has no reachable PostgreSQL service, so it does not yet satisfy the PostgreSQL
deployment requirement.

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
