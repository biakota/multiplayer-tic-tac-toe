# Gridlock — Multiplayer Tic-Tac-Toe

A responsive, real-time two-player Tic-Tac-Toe application. React + TypeScript frontend, FastAPI WebSocket backend, and Redis-backed room state.

## Features

- Create private six-character rooms and share the code.
- Join from another device/browser.
- Server-authoritative turns, move validation, win/draw detection.
- Real-time state broadcasts over WebSockets.
- Rematch requires both players to vote.
- Redis TTL automatically expires abandoned rooms.
- Responsive dark gaming UI.

## Architecture and important limitations

Redis stores room state so it survives API process restarts and can be shared across API instances. The initial implementation uses a single-process WebSocket connection manager; for horizontally scaled deployment, add Redis Pub/Sub (or a managed WebSocket gateway) so messages reach clients connected to different API instances. A production hardening pass should also add authenticated, expiring player credentials, rate limiting, schema validation for all WebSocket event payloads, and automated reconnect/rejoin UX. Do not deploy multiple API replicas until cross-instance WebSocket fan-out is implemented.

The current player ID is a high-entropy bearer token returned at room creation/join and stored in sessionStorage. Treat it as a secret.

## Requirements

- Python 3.11+
- Node.js 20+
- Docker Desktop / Docker Engine with Compose
- Redis 7 (Docker Compose starts it for you)

## Run locally

### 1. Start Redis and API

From the repository root:

```bash
docker compose up --build
```

API: http://localhost:8000  
Health: http://localhost:8000/health  
OpenAPI: http://localhost:8000/docs

Alternatively, run the API without Docker:

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements-dev.txt
export REDIS_URL=redis://localhost:6379/0
export CORS_ORIGINS=http://localhost:5173
uvicorn app.main:app --reload
```

### 2. Start frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

If the API is hosted elsewhere, set `VITE_API_URL` before starting/building, for example:

```bash
VITE_API_URL=https://your-api.onrender.com npm run build
```

The frontend derives the WebSocket URL by converting `https://` to `wss://`.

## Tests

```bash
cd backend
pip install -r requirements-dev.txt
PYTHONPATH=. python -m unittest discover -s tests -v
```

Game rules and service tests use Python's standard `unittest`. Redis-backed API/WebSocket integration tests should be added against a disposable Redis instance before a public production release.

## Deploy

### Redis

Create a managed Redis-compatible database (for example, Redis Cloud or a hosting provider's managed Redis). Use its private/internal connection URL where possible. Enable TLS if required by the provider (`rediss://...`).

### FastAPI backend

Deploy `backend/` as a Docker service using `backend/Dockerfile`, or deploy from the repository root with the backend as the build context. Configure:

- `REDIS_URL`: managed Redis connection string
- `CORS_ORIGINS`: exact frontend origin, e.g. `https://your-game.vercel.app`
- `ROOM_TTL_SECONDS`: optional, defaults to 86400

Health check path: `/health`. Start command if not using Docker:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Ensure the host supports persistent WebSocket connections. Use one API instance for this initial version because WebSocket fan-out is process-local.

### React frontend

Deploy `frontend/` to Vercel. Set:

- Root directory: `frontend`
- Build command: `npm run build`
- Output directory: `dist`
- Environment variable `VITE_API_URL`: public HTTPS API URL

Redeploy after setting environment variables.

## Two-device acceptance test

1. Open the deployed frontend on Device A.
2. Select **Create a room** and copy the six-character code.
3. Open the public frontend on Device B (or a private/incognito browser).
4. Enter the code and join.
5. Confirm both clients show the same board and player assignments.
6. Play alternating moves; confirm the other screen updates immediately.
7. Test occupied-cell and out-of-turn rejection.
8. Complete a win and a draw in separate games.
9. Request a rematch from both clients.
10. Refresh/reconnect and verify the documented session behavior.

## WebSocket event protocol

Client messages:
- `{"type":"make_move","row":0,"col":1}`
- `{"type":"request_rematch"}`
- `{"type":"leave_room"}`

Server messages:
- `{"type":"state","game":{...}}`
- `{"type":"error","message":"..."}`

The server sends `player_disconnected` to the opponent when a socket closes unexpectedly.
