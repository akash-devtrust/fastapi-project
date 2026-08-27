# Simple FastAPI Todo API

A small, beginner-friendly REST API built with Python, FastAPI, and SQLite. It stores todos in a SQLite database file, so data stays saved after the server restarts.

## Project Structure

```text
fastapi-project/
├── app/
│   ├── __init__.py
│   ├── database.py
│   ├── db_models.py
│   ├── main.py
│   └── models.py
├── .gitignore
├── requirements.txt
├── README.md
└── .env.example
```

## Create and Activate a Virtual Environment

From inside the `fastapi-project` directory:

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Set Up SQLite

SQLite does not need a separate database server, username, or password. The app uses this database URL:

```env
DATABASE_URL=sqlite:///./todos.db
```

Create a local `.env` file from the example file if it does not exist yet:

```bash
cp .env.example .env
```

When the API starts, it will automatically create:

```text
todos.db
```

It will also create the `todos` table automatically.

SQLite works well for local development and PythonAnywhere free hosting.

## Run the API

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Swagger documentation will be available at:

```text
http://127.0.0.1:8000/docs
```

## Available Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/` | Welcome message |
| GET | `/health` | API health status |
| GET | `/todos` | Get all todos |
| GET | `/todos/{todo_id}` | Get one todo |
| POST | `/todos` | Create a todo |
| PUT | `/todos/{todo_id}` | Update a todo |
| DELETE | `/todos/{todo_id}` | Delete a todo |
| POST | `/api/analytics/visit` | Count an anonymous unique visitor |
| POST | `/api/analytics/heartbeat` | Update an active listener session |
| POST | `/api/analytics/play` | Count a song play with session deduplication |
| GET | `/api/analytics/stats` | Get total visitors, active listeners, and total plays |
| GET | `/api/analytics/songs` | Get all 30 songs in order with play counts |

## Music Player Analytics

The `/api/analytics` endpoints are designed for the static GitHub Pages music player at:

```text
https://akash-devtrust.github.io/music-player/
```

They store only anonymous identifiers, song IDs, and timestamps. The API does not store raw IP addresses, browser fingerprints, user-agent strings, names, emails, or location data.

### Environment Variables

```env
DATABASE_URL=sqlite:///./todos.db
ACTIVE_LISTENER_TIMEOUT=60
PLAY_DEDUP_SECONDS=30
FRONTEND_ORIGINS=https://akash-devtrust.github.io
```

- `ACTIVE_LISTENER_TIMEOUT` controls how long a heartbeat remains active.
- `PLAY_DEDUP_SECONDS` controls how soon the same session can count another play of the same song.
- `FRONTEND_ORIGINS` is a comma-separated list of origins allowed by CORS.

### Database Tables

The app uses the existing SQLAlchemy setup and creates these tables automatically on startup:

- `analytics_visitors`
- `analytics_daily_visitors`
- `analytics_sessions`
- `analytics_song_play_counts`
- `analytics_session_song_plays`

### curl Examples

Record a visit:

```bash
curl -X POST http://127.0.0.1:8000/api/analytics/visit \
  -H "Content-Type: application/json" \
  -d '{"visitor_id":"visitor-123456789"}'
```

Send a heartbeat:

```bash
curl -X POST http://127.0.0.1:8000/api/analytics/heartbeat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"session-123456789","song_id":1}'
```

Record a play:

```bash
curl -X POST http://127.0.0.1:8000/api/analytics/play \
  -H "Content-Type: application/json" \
  -d '{"session_id":"session-123456789","song_id":1}'
```

Get aggregate stats:

```bash
curl http://127.0.0.1:8000/api/analytics/stats
```

Get song play counts:

```bash
curl http://127.0.0.1:8000/api/analytics/songs
```

### GitHub Pages JavaScript Example

```js
const API_BASE_URL = "https://YOUR-BACKEND-DOMAIN.example.com";

const visitorId =
  localStorage.getItem("mehfil_visitor_id") || crypto.randomUUID();

localStorage.setItem("mehfil_visitor_id", visitorId);

const sessionId = crypto.randomUUID();
let heartbeatTimer = null;

async function postJson(path, body) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return response.json();
}

async function recordVisit() {
  return postJson("/api/analytics/visit", { visitor_id: visitorId });
}

async function recordPlay(songId) {
  return postJson("/api/analytics/play", {
    session_id: sessionId,
    song_id: songId,
  });
}

async function sendHeartbeat(songId) {
  return postJson("/api/analytics/heartbeat", {
    session_id: sessionId,
    song_id: songId,
  });
}

function startHeartbeat(getCurrentSongId) {
  stopHeartbeat();
  sendHeartbeat(getCurrentSongId()).catch(console.error);
  heartbeatTimer = setInterval(() => {
    sendHeartbeat(getCurrentSongId()).catch(console.error);
  }, 25000);
}

function stopHeartbeat() {
  if (heartbeatTimer !== null) {
    clearInterval(heartbeatTimer);
    heartbeatTimer = null;
  }
}

recordVisit().catch(console.error);

// Call recordPlay(newSongId) when playback starts or changes to a new song.
// Call startHeartbeat(() => currentSongId) while actively playing.
// Call stopHeartbeat() when paused, stopped, or the page is unloading.
```

The frontend should keep song #1 as the starting song and keep the existing 30-song order unchanged.

## Test the API

Open a second terminal while the server is running.

### Welcome Message

```bash
curl http://127.0.0.1:8000/
```

### Health Check

```bash
curl http://127.0.0.1:8000/health
```

### Create a Todo

```bash
curl -X POST http://127.0.0.1:8000/todos \
  -H "Content-Type: application/json" \
  -d '{"title":"Learn FastAPI","description":"Build a simple Todo API","completed":false}'
```

### Get All Todos

```bash
curl http://127.0.0.1:8000/todos
```

### Get One Todo

```bash
curl http://127.0.0.1:8000/todos/1
```

### Update a Todo

```bash
curl -X PUT http://127.0.0.1:8000/todos/1 \
  -H "Content-Type: application/json" \
  -d '{"title":"Learn FastAPI","description":"Update the Todo API","completed":true}'
```

### Delete a Todo

```bash
curl -X DELETE http://127.0.0.1:8000/todos/1
```

### Confirm Deleted Todo Returns 404

```bash
curl http://127.0.0.1:8000/todos/1
```

## Initialize Git

```bash
git init
git add .
git commit -m "Create simple FastAPI Todo API"
```

## Push to GitHub

Create a new empty repository on GitHub first. Then run:

```bash
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```

## Server Deployment

On the server, pull the latest code:

```bash
cd ~/fastapi-project
git pull origin main
```

Then reload the ASGI website:

```bash
pa website reload --domain kinady.pythonanywhere.com
```

After deployment, confirm the analytics API appears in:

```text
https://YOUR-BACKEND-DOMAIN.example.com/docs
https://YOUR-BACKEND-DOMAIN.example.com/openapi.json
```
