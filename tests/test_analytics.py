import os
import subprocess
import sys
import time
from datetime import timedelta
from pathlib import Path

import httpx2
import pytest

os.environ["DATABASE_URL"] = f"sqlite:///{Path('/tmp/analytics_test.db')}"
os.environ["FRONTEND_ORIGINS"] = "https://akash-devtrust.github.io"
os.environ["ACTIVE_LISTENER_TIMEOUT"] = "60"
os.environ["PLAY_DEDUP_SECONDS"] = "30"

from app.analytics import utc_now
from app.database import Base, SessionLocal, engine
from app.db_models import AnalyticsSessionDB, AnalyticsSessionSongPlayDB


PORT = int(os.getenv("TEST_API_PORT", "8765"))
API_BASE_URL = f"http://127.0.0.1:{PORT}"


@pytest.fixture(scope="session", autouse=True)
def api_server():
    env = os.environ.copy()
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(PORT),
        ],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    deadline = time.time() + 15
    while time.time() < deadline:
        if process.poll() is not None:
            stderr = process.stderr.read() if process.stderr else ""
            raise RuntimeError(f"API server exited early: {stderr}")
        try:
            response = httpx2.get(f"{API_BASE_URL}/health", timeout=1)
            if response.status_code == 200:
                break
        except httpx2.HTTPError:
            time.sleep(0.2)
    else:
        process.terminate()
        raise RuntimeError("API server did not start in time")

    yield

    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


@pytest.fixture(autouse=True)
def reset_database(api_server):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def post_json(path: str, payload: dict) -> httpx2.Response:
    return httpx2.post(f"{API_BASE_URL}{path}", json=payload, timeout=5)


def get(path: str) -> httpx2.Response:
    return httpx2.get(f"{API_BASE_URL}{path}", timeout=5)


def test_visitor_is_counted_once():
    response = post_json(
        "/api/analytics/visit", {"visitor_id": "visitor-123456"}
    )
    assert response.status_code == 200
    assert response.json() == {"total_visitors": 1}

    response = post_json(
        "/api/analytics/visit", {"visitor_id": "visitor-123456"}
    )
    assert response.status_code == 200
    assert response.json() == {"total_visitors": 1}


def test_heartbeat_creates_active_listener_and_updates_last_seen():
    response = post_json(
        "/api/analytics/heartbeat",
        {"session_id": "session-123456", "song_id": 1},
    )
    assert response.status_code == 200
    assert response.json() == {"active_listeners": 1}

    db = SessionLocal()
    try:
        session = (
            db.query(AnalyticsSessionDB)
            .filter(AnalyticsSessionDB.session_id == "session-123456")
            .first()
        )
        assert session is not None
        original_last_seen = session.last_seen
        session.last_heartbeat_at = utc_now() - timedelta(seconds=5)
        db.commit()
    finally:
        db.close()

    response = post_json(
        "/api/analytics/heartbeat",
        {"session_id": "session-123456", "song_id": 2},
    )
    assert response.status_code == 200

    db = SessionLocal()
    try:
        session = (
            db.query(AnalyticsSessionDB)
            .filter(AnalyticsSessionDB.session_id == "session-123456")
            .first()
        )
        assert session.song_id == 2
        assert session.last_seen != original_last_seen
    finally:
        db.close()


def test_expired_heartbeat_is_not_active():
    response = post_json(
        "/api/analytics/heartbeat",
        {"session_id": "session-expired", "song_id": 1},
    )
    assert response.status_code == 200

    db = SessionLocal()
    try:
        session = (
            db.query(AnalyticsSessionDB)
            .filter(AnalyticsSessionDB.session_id == "session-expired")
            .first()
        )
        expired_time = utc_now() - timedelta(seconds=120)
        session.last_seen = expired_time
        session.last_heartbeat_at = expired_time
        db.commit()
    finally:
        db.close()

    response = get("/api/analytics/stats")
    assert response.status_code == 200
    assert response.json()["active_listeners"] == 0


def test_extremely_frequent_heartbeat_is_rate_limited():
    payload = {"session_id": "session-rate-limit", "song_id": 1}
    assert post_json("/api/analytics/heartbeat", payload).status_code == 200

    response = post_json("/api/analytics/heartbeat", payload)
    assert response.status_code == 429


def test_song_play_increments_and_deduplicates_rapid_repeats():
    payload = {"session_id": "session-play-123", "song_id": 1}
    response = post_json("/api/analytics/play", payload)
    assert response.status_code == 200
    assert response.json() == {"song_id": 1, "plays": 1}

    response = post_json("/api/analytics/play", payload)
    assert response.status_code == 200
    assert response.json() == {"song_id": 1, "plays": 1}

    db = SessionLocal()
    try:
        session_play = (
            db.query(AnalyticsSessionSongPlayDB)
            .filter(
                AnalyticsSessionSongPlayDB.session_id == "session-play-123",
                AnalyticsSessionSongPlayDB.song_id == 1,
            )
            .first()
        )
        session_play.last_played_at = utc_now() - timedelta(seconds=31)
        db.commit()
    finally:
        db.close()

    response = post_json("/api/analytics/play", payload)
    assert response.status_code == 200
    assert response.json() == {"song_id": 1, "plays": 2}


def test_invalid_song_id_is_rejected():
    for song_id in (0, 31):
        response = post_json(
            "/api/analytics/play",
            {"session_id": "session-invalid-song", "song_id": song_id},
        )
        assert response.status_code == 422


def test_invalid_session_id_is_rejected():
    response = post_json(
        "/api/analytics/heartbeat",
        {"session_id": "bad", "song_id": 1},
    )
    assert response.status_code == 422


def test_stats_endpoint_works():
    post_json("/api/analytics/visit", {"visitor_id": "visitor-stats-1"})
    post_json(
        "/api/analytics/heartbeat",
        {"session_id": "session-stats-1", "song_id": 1},
    )
    post_json(
        "/api/analytics/play",
        {"session_id": "session-stats-1", "song_id": 1},
    )

    response = get("/api/analytics/stats")
    assert response.status_code == 200
    assert response.json() == {
        "total_visitors": 1,
        "active_listeners": 1,
        "total_plays": 1,
    }


def test_all_song_ids_are_accepted_and_songs_are_returned_in_order():
    for song_id in range(1, 31):
        response = post_json(
            "/api/analytics/play",
            {"session_id": f"session-song-{song_id}", "song_id": song_id},
        )
        assert response.status_code == 200

    response = get("/api/analytics/songs")
    assert response.status_code == 200
    songs = response.json()
    assert [song["song_id"] for song in songs] == list(range(1, 31))
    assert songs[0] == {
        "song_id": 1,
        "title": "Hungama Hai Kyon Barpa",
        "artist": "Ghulam Ali",
        "plays": 1,
    }
    assert songs[-1]["title"] == "Ahista"
    assert songs[-1]["artist"] == "Pankaj Udhas"


def test_cors_allows_github_pages_origin():
    response = httpx2.options(
        f"{API_BASE_URL}/api/analytics/stats",
        headers={
            "Origin": "https://akash-devtrust.github.io",
            "Access-Control-Request-Method": "GET",
        },
        timeout=5,
    )
    assert response.status_code == 200
    assert (
        response.headers["access-control-allow-origin"]
        == "https://akash-devtrust.github.io"
    )
