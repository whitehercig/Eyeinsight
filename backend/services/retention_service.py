"""Configurable retention cleanup for public-demo session data."""

from __future__ import annotations

from datetime import datetime, timedelta
import os
from pathlib import Path
import shutil

from sqlalchemy.orm import Session as DBSession

from models import AnalysisResult, Session
from services.video_feature_service import FEATURES_DIR


def purge_expired_sessions(db: DBSession, now: datetime | None = None) -> int:
    ttl_hours = _ttl_hours()
    if ttl_hours <= 0:
        return 0
    cutoff = (now or datetime.utcnow()) - timedelta(hours=ttl_hours)
    expired = db.query(Session).filter(Session.created_at < cutoff).all()
    for session in expired:
        result = db.query(AnalysisResult).filter(AnalysisResult.session_id == session.id).first()
        if result:
            db.delete(result)
        if session.video_path:
            Path(session.video_path).unlink(missing_ok=True)
        shutil.rmtree(Path(FEATURES_DIR) / session.id, ignore_errors=True)
        db.delete(session)
    if expired:
        db.commit()
    return len(expired)


def _ttl_hours() -> float:
    try:
        return max(0.0, float(os.getenv("EYEINSIGHT_SESSION_TTL_HOURS", "24")))
    except ValueError:
        return 24.0
