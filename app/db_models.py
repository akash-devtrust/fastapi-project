from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from app.database import Base


class TodoDB(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    completed = Column(Boolean, default=False, nullable=False)
    priority = Column(String(20), default="medium", nullable=False)
    due_date = Column(Date, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class AnalyticsVisitorDB(Base):
    __tablename__ = "analytics_visitors"

    id = Column(Integer, primary_key=True, index=True)
    visitor_id = Column(String(128), unique=True, index=True, nullable=False)
    first_seen = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_seen = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class AnalyticsDailyVisitorDB(Base):
    __tablename__ = "analytics_daily_visitors"
    __table_args__ = (
        UniqueConstraint("visitor_id", "visit_date", name="uq_daily_visitor"),
    )

    id = Column(Integer, primary_key=True, index=True)
    visitor_id = Column(String(128), index=True, nullable=False)
    visit_date = Column(Date, index=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class AnalyticsSessionDB(Base):
    __tablename__ = "analytics_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(128), unique=True, index=True, nullable=False)
    song_id = Column(Integer, index=True, nullable=False)
    last_seen = Column(DateTime(timezone=True), index=True, nullable=False)
    last_heartbeat_at = Column(DateTime(timezone=True), nullable=False)


class AnalyticsSongPlayCountDB(Base):
    __tablename__ = "analytics_song_play_counts"

    id = Column(Integer, primary_key=True, index=True)
    song_id = Column(Integer, unique=True, index=True, nullable=False)
    plays = Column(Integer, default=0, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class AnalyticsSessionSongPlayDB(Base):
    __tablename__ = "analytics_session_song_plays"
    __table_args__ = (
        UniqueConstraint("session_id", "song_id", name="uq_session_song_play"),
    )

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(128), index=True, nullable=False)
    song_id = Column(Integer, index=True, nullable=False)
    last_played_at = Column(DateTime(timezone=True), index=True, nullable=False)
