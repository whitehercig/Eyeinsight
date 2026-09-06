from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from routes import analysis
from routes.analysis import _delete_source_video


class FakeDatabase:
    def __init__(self) -> None:
        self.commits = 0

    def commit(self) -> None:
        self.commits += 1


class FakeQuery:
    def __init__(self, value) -> None:
        self.value = value

    def filter(self, *_args):
        return self

    def first(self):
        return self.value


class AnalysisDatabase(FakeDatabase):
    def __init__(self, session, result=None) -> None:
        super().__init__()
        self.values = [session, result]

    def query(self, _model):
        return FakeQuery(self.values.pop(0))


def test_source_video_is_deleted_by_default(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("EYEINSIGHT_DELETE_SOURCE_VIDEO", raising=False)
    video_path = tmp_path / "session.webm"
    video_path.write_bytes(b"video")
    session = SimpleNamespace(video_path=str(video_path))
    database = FakeDatabase()

    _delete_source_video(session, database)

    assert not video_path.exists()
    assert session.video_path is None
    assert database.commits == 1


def test_source_video_can_be_retained_for_approved_research(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("EYEINSIGHT_DELETE_SOURCE_VIDEO", "false")
    video_path = tmp_path / "session.webm"
    video_path.write_bytes(b"video")
    session = SimpleNamespace(video_path=str(video_path))
    database = FakeDatabase()

    _delete_source_video(session, database)

    assert video_path.exists()
    assert session.video_path == str(video_path)
    assert database.commits == 0


def test_processing_session_rejects_duplicate_analysis() -> None:
    session = SimpleNamespace(status="processing", video_path="session.webm")
    database = AnalysisDatabase(session)

    with pytest.raises(HTTPException) as raised:
        analysis.analyze_session("session-id", retry=False, db=database)

    assert raised.value.status_code == 409
    assert raised.value.detail == "analysis_in_progress"


def test_failed_extraction_sets_recoverable_session_status(monkeypatch) -> None:
    session = SimpleNamespace(status="uploaded", video_path="session.webm")
    database = AnalysisDatabase(session)
    monkeypatch.setattr(analysis, "extract_video_features", lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("video_decode_failed")))

    with pytest.raises(HTTPException) as raised:
        analysis.analyze_session("session-id", retry=False, db=database)

    assert raised.value.status_code == 422
    assert session.status == "analysis_failed"
    assert database.commits == 2
