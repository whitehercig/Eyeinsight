from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, Session
from services import retention_service


def test_expired_sessions_and_artifacts_are_removed(tmp_path: Path, monkeypatch) -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    database = sessionmaker(bind=engine)()
    now = datetime(2026, 9, 4, 12, 0, 0)
    expired = Session(id="expired", status="analyzed", created_at=now - timedelta(hours=25))
    current = Session(id="current", status="analyzed", created_at=now - timedelta(hours=2))
    database.add_all([expired, current])
    database.commit()
    features_dir = tmp_path / "features"
    (features_dir / expired.id).mkdir(parents=True)
    (features_dir / expired.id / "session_features.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(retention_service, "FEATURES_DIR", str(features_dir))
    monkeypatch.setenv("EYEINSIGHT_SESSION_TTL_HOURS", "24")

    removed = retention_service.purge_expired_sessions(database, now=now)

    assert removed == 1
    assert database.get(Session, expired.id) is None
    assert database.get(Session, current.id) is not None
    assert not (features_dir / expired.id).exists()


def test_non_positive_ttl_disables_cleanup(monkeypatch) -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    database = sessionmaker(bind=engine)()
    database.add(Session(id="kept", status="created", created_at=datetime(2020, 1, 1)))
    database.commit()
    monkeypatch.setenv("EYEINSIGHT_SESSION_TTL_HOURS", "0")

    assert retention_service.purge_expired_sessions(database, now=datetime(2026, 9, 4)) == 0
    assert database.get(Session, "kept") is not None
