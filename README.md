SARGAM(personal music stremaing app)

The actual music folder can be configured through the backend environment settings.

Supported audio formats include:

MP3
FLAC
M4A
WAV

Audio files remain on the local filesystem while SQLite stores the required application and catalog data.

1. Backend Setup
cd backend
python -m venv .venv

Activate the virtual environment on Windows:

.\.venv\Scripts\activate

Install dependencies:

pip install -r requirements.txt

Start the FastAPI server:

python -m uvicorn main:app --host 0.0.0.0 --port 8000

The backend will be available at:

http://localhost:8000
2. Frontend Setup

Open another terminal:

cd frontend
npm install
npm run dev -- --host 0.0.0.0

The Vite development server will be available on the configured development port.

3. Android Setup

Sargam uses Capacitor to run the React application as an Android application.

Sync the Android project:

npx cap sync android

For development, the Android device and laptop should be connected to the same local network.

Example:

Vite:
http://<LAPTOP-IP>:5175

FastAPI:
http://<LAPTOP-IP>:8000

Replace <LAPTOP-IP> with the laptop's current local network IP address.


The laptop acts as the music server. The Android application communicates with the FastAPI backend over the local network and streams audio from the laptop's music library.

API

The application uses REST APIs for communication between the Android frontend and FastAPI backend.

Examples include:

GET /api/songs/
GET /api/search/?q=<query>
GET /api/songs/{song_id}/stream

The Android application uses the laptop's LAN address when communicating with the backend. localhost should not be used from the Android device because it refers to the phone itself.

Development

For local development, run both the backend and frontend servers.

Backend:

cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000

Frontend:

cd frontend
npm run dev -- --host 0.0.0.0

The Android application can then connect to the development servers through the laptop's local network address.

Project Status

🚧 Actively Developed

Sargam is a personal full-stack Android project focused on mobile application development, REST APIs, client-server architecture, local media streaming, database management, authentication, and responsive UI development.

Future Improvements
Background playback and Android media controls
Improved music recommendations
Automatic music-server discovery
Offline playback
Enhanced playlist management
Improved library organization
Production deployment

**One correction from your old README:** I deliberately removed **PostgreSQL, SQLAlchemy, and JWT** because your current project uses **SQLite**, and the README should accurately represent what you've actually built.

Available next action: :contentReference[oaicite:0]{index=0}


Architecture:

                    Android Phone
                         │
                         │ Wi-Fi
                         ▼
                React + Capacitor
                         │
                         │ REST APIs
                         ▼
                   FastAPI Backend
                    ┌────┴────┐
                    │         │
                    ▼         ▼
                 SQLite    Music Files
                              │
                              ▼
                       Local Music Folder



The laptop acts as the music server. The Android application communicates with the FastAPI backend over the local network and streams music from the laptop's music library.





Getting Started
Backend Setup
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

Start the FastAPI server:

python -m uvicorn main:app --host 0.0.0.0 --port 8000
Frontend Setup

Open another terminal:

cd frontend
npm install
npm run dev -- --host 0.0.0.0
Android Setup

Sargam uses Capacitor to run the React application as an Android application.

Sync the Android project:

npx cap sync android

For development over Wi-Fi, connect the Android device and laptop to the same local network.

Example:

Vite:
http://<LAPTOP-IP>:5175

FastAPI:
http://<LAPTOP-IP>:8000

Replace <LAPTOP-IP> with the laptop's current local network IP address.

API

The Android application communicates with the FastAPI backend through REST APIs.

Example endpoints:

GET /api/songs/
GET /api/search/?q=<query>
GET /api/songs/{song_id}/stream
Development

Run the backend and frontend servers during development.

Backend:

cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000

Frontend:

cd frontend
npm run dev -- --host 0.0.0.0

The Android application can then communicate with the development servers through the laptop's local network address.

Project Status

🚧 Actively Developed

Sargam is a personal full-stack Android project focused on mobile application development, REST APIs, client-server architecture, local media streaming, database management, authentication, and responsive UI development.

Future Improvements
Background playback with Android media controls
Improved music recommendations
Automatic music-server discovery
Offline playback
Enhanced playlist and library management