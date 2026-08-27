import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.db_models import (
    AnalyticsDailyVisitorDB,
    AnalyticsSessionDB,
    AnalyticsSessionSongPlayDB,
    AnalyticsSongPlayCountDB,
    AnalyticsVisitorDB,
)
from app.models import (
    AnalyticsStatsResponse,
    HeartbeatRequest,
    HeartbeatResponse,
    PlayRequest,
    PlayResponse,
    SongStatsResponse,
    VisitRequest,
    VisitResponse,
)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

HEARTBEAT_MIN_SECONDS = 2

SONGS: tuple[dict[str, int | str], ...] = (
    {"song_id": 1, "title": "Hungama Hai Kyon Barpa", "artist": "Ghulam Ali"},
    {"song_id": 2, "title": "Chupke Chupke Raat Din", "artist": "Ghulam Ali"},
    {"song_id": 3, "title": "Patta Patta Boota Boota", "artist": "Ghulam Ali"},
    {"song_id": 4, "title": "Dil Mein Ek Lehar Si Uthi Hai", "artist": "Ghulam Ali"},
    {"song_id": 5, "title": "Yeh Dil Yeh Pagal Dil Mera", "artist": "Ghulam Ali"},
    {"song_id": 6, "title": "Awaargi", "artist": "Ghulam Ali"},
    {"song_id": 7, "title": "Main Nazar Se Pee Raha Hoon", "artist": "Ghulam Ali"},
    {"song_id": 8, "title": "Ranjish Hi Sahi", "artist": "Mehdi Hassan"},
    {"song_id": 9, "title": "Gulon Mein Rang Bhare", "artist": "Mehdi Hassan"},
    {
        "song_id": 10,
        "title": "Mujhe Tum Nazar Se Gira To Rahe Ho",
        "artist": "Mehdi Hassan",
    },
    {
        "song_id": 11,
        "title": "Rafta Rafta Woh Meri Hasti Ka Samaan Ho Gaye",
        "artist": "Mehdi Hassan",
    },
    {
        "song_id": 12,
        "title": "Zindagi Mein To Sabhi Pyar Kiya Karte Hain",
        "artist": "Mehdi Hassan",
    },
    {"song_id": 13, "title": "Shola Tha Jalbujha Hoon", "artist": "Mehdi Hassan"},
    {"song_id": 14, "title": "Ab Ke Hum Bichhde", "artist": "Mehdi Hassan"},
    {
        "song_id": 15,
        "title": "Mohabbat Karne Wale Kam Na Honge",
        "artist": "Mehdi Hassan",
    },
    {"song_id": 16, "title": "Aaj Jaane Ki Zid Na Karo", "artist": "Farida Khanum"},
    {
        "song_id": 17,
        "title": "Woh Ishq Jo Hum Se Rooth Gaya",
        "artist": "Amanat Ali Khan",
    },
    {"song_id": 18, "title": "Insha Ji Utho Ab Kooch Karo", "artist": "Amanat Ali Khan"},
    {"song_id": 19, "title": "Tere Ishq Nachaya", "artist": "Abida Parveen"},
    {"song_id": 20, "title": "Yaar Ko Humne Ja Ba Ja Dekha", "artist": "Abida Parveen"},
    {"song_id": 21, "title": "Main Naraye Mastana", "artist": "Abida Parveen"},
    {"song_id": 22, "title": "Chaap Tilak", "artist": "Abida Parveen"},
    {
        "song_id": 23,
        "title": "Aap Ki Yaad Aati Rahi Raat Bhar",
        "artist": "Jagjit Singh",
    },
    {"song_id": 24, "title": "Tum Itna Jo Muskura Rahe Ho", "artist": "Jagjit Singh"},
    {"song_id": 25, "title": "Hothon Se Chhu Lo Tum", "artist": "Jagjit Singh"},
    {"song_id": 26, "title": "Kal Chaudhvin Ki Raat Thi", "artist": "Jagjit Singh"},
    {"song_id": 27, "title": "Jhuki Jhuki Si Nazar", "artist": "Jagjit Singh"},
    {"song_id": 28, "title": "Koi Fariyaad", "artist": "Jagjit Singh"},
    {"song_id": 29, "title": "Woh Kagaz Ki Kashti", "artist": "Jagjit Singh"},
    {"song_id": 30, "title": "Ahista", "artist": "Pankaj Udhas"},
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def active_listener_timeout() -> int:
    return env_int("ACTIVE_LISTENER_TIMEOUT", 60)


def play_dedup_seconds() -> int:
    return env_int("PLAY_DEDUP_SECONDS", 30)


def seconds_since(value: datetime, now: datetime) -> float:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return (now - value).total_seconds()


def active_listener_count(db: Session, now: datetime | None = None) -> int:
    now = now or utc_now()
    active_after = now - timedelta(seconds=active_listener_timeout())
    return (
        db.query(func.count(AnalyticsSessionDB.id))
        .filter(AnalyticsSessionDB.last_seen >= active_after)
        .scalar()
        or 0
    )


@router.post(
    "/visit",
    response_model=VisitResponse,
    summary="Record an anonymous visit",
    description=(
        "Records a stable anonymous visitor identifier without storing IP "
        "addresses, user agents, or other personal information."
    ),
)
def record_visit(visit: VisitRequest, db: Session = Depends(get_db)) -> VisitResponse:
    now = utc_now()
    visitor = (
        db.query(AnalyticsVisitorDB)
        .filter(AnalyticsVisitorDB.visitor_id == visit.visitor_id)
        .first()
    )

    if visitor is None:
        visitor = AnalyticsVisitorDB(
            visitor_id=visit.visitor_id,
            first_seen=now,
            last_seen=now,
        )
        db.add(visitor)
    else:
        visitor.last_seen = now

    daily_visitor = (
        db.query(AnalyticsDailyVisitorDB)
        .filter(
            AnalyticsDailyVisitorDB.visitor_id == visit.visitor_id,
            AnalyticsDailyVisitorDB.visit_date == now.date(),
        )
        .first()
    )
    if daily_visitor is None:
        db.add(
            AnalyticsDailyVisitorDB(
                visitor_id=visit.visitor_id,
                visit_date=now.date(),
                created_at=now,
            )
        )

    db.commit()
    total_visitors = db.query(func.count(AnalyticsVisitorDB.id)).scalar() or 0
    return VisitResponse(total_visitors=total_visitors)


@router.post(
    "/heartbeat",
    response_model=HeartbeatResponse,
    summary="Update an active listener heartbeat",
    description=(
        "Updates the anonymous listener session and returns the number of "
        "sessions seen within ACTIVE_LISTENER_TIMEOUT seconds."
    ),
)
def record_heartbeat(
    heartbeat: HeartbeatRequest, db: Session = Depends(get_db)
) -> HeartbeatResponse:
    now = utc_now()
    session = (
        db.query(AnalyticsSessionDB)
        .filter(AnalyticsSessionDB.session_id == heartbeat.session_id)
        .first()
    )

    if session is not None:
        if (
            session.song_id == heartbeat.song_id
            and seconds_since(session.last_heartbeat_at, now) < HEARTBEAT_MIN_SECONDS
        ):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Heartbeat too frequent",
            )
        session.song_id = heartbeat.song_id
        session.last_seen = now
        session.last_heartbeat_at = now
    else:
        db.add(
            AnalyticsSessionDB(
                session_id=heartbeat.session_id,
                song_id=heartbeat.song_id,
                last_seen=now,
                last_heartbeat_at=now,
            )
        )

    db.commit()
    return HeartbeatResponse(active_listeners=active_listener_count(db, now))


@router.post(
    "/play",
    response_model=PlayResponse,
    summary="Record a song play",
    description=(
        "Increments a song play count unless the same anonymous session already "
        "counted the same song within PLAY_DEDUP_SECONDS seconds."
    ),
)
def record_play(play: PlayRequest, db: Session = Depends(get_db)) -> PlayResponse:
    now = utc_now()
    session_song = (
        db.query(AnalyticsSessionSongPlayDB)
        .filter(
            AnalyticsSessionSongPlayDB.session_id == play.session_id,
            AnalyticsSessionSongPlayDB.song_id == play.song_id,
        )
        .first()
    )

    should_count = session_song is None or seconds_since(
        session_song.last_played_at, now
    ) >= play_dedup_seconds()

    play_count = (
        db.query(AnalyticsSongPlayCountDB)
        .filter(AnalyticsSongPlayCountDB.song_id == play.song_id)
        .first()
    )
    if play_count is None:
        play_count = AnalyticsSongPlayCountDB(song_id=play.song_id, plays=0)
        db.add(play_count)
        db.flush()

    if should_count:
        play_count.plays += 1
        play_count.updated_at = now
        if session_song is None:
            db.add(
                AnalyticsSessionSongPlayDB(
                    session_id=play.session_id,
                    song_id=play.song_id,
                    last_played_at=now,
                )
            )
        else:
            session_song.last_played_at = now

    db.commit()
    db.refresh(play_count)
    return PlayResponse(song_id=play.song_id, plays=play_count.plays)


@router.get(
    "/stats",
    response_model=AnalyticsStatsResponse,
    summary="Get aggregate analytics statistics",
    description="Returns total unique visitors, active listeners, and total song plays.",
)
def get_stats(db: Session = Depends(get_db)) -> AnalyticsStatsResponse:
    total_visitors = db.query(func.count(AnalyticsVisitorDB.id)).scalar() or 0
    total_plays = db.query(func.sum(AnalyticsSongPlayCountDB.plays)).scalar() or 0

    return AnalyticsStatsResponse(
        total_visitors=total_visitors,
        active_listeners=active_listener_count(db),
        total_plays=total_plays,
    )


@router.get(
    "/songs",
    response_model=list[SongStatsResponse],
    summary="Get song play counts",
    description="Returns the 30 music player songs in order with their play counts.",
)
def get_song_stats(db: Session = Depends(get_db)) -> list[SongStatsResponse]:
    play_counts = {
        row.song_id: row.plays for row in db.query(AnalyticsSongPlayCountDB).all()
    }
    return [
        SongStatsResponse(
            song_id=int(song["song_id"]),
            title=str(song["title"]),
            artist=str(song["artist"]),
            plays=play_counts.get(int(song["song_id"]), 0),
        )
        for song in SONGS
    ]
