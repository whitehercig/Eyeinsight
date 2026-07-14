"""
Session management routes:
- POST /api/sessions         — create a new screening session
- POST /api/sessions/{id}/upload-video — upload recorded video
"""

import os
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, File, status
from sqlalchemy.orm import Session as DBSession
import aiofiles

from database import get_db
from models import AnalysisResult, Session
from schemas import SessionResponse
from services.video_feature_service import FEATURES_DIR

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
UPLOADS_DIR = os.path.join(os.getenv("EYEINSIGHT_DATA_DIR", BASE_DIR), "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)
MAX_UPLOAD_BYTES = 80 * 1024 * 1024
ALLOWED_SUFFIXES = {".webm", ".mp4", ".mov"}


@router.post("", response_model=SessionResponse)
def create_session(db: DBSession = Depends(get_db)):
    """
    Create a new screening session and return its ID.
    Called before recording begins so we have an ID to associate the video with.
    """
    session = Session(id=str(uuid.uuid4()), status="created")
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: str, db: DBSession = Depends(get_db)) -> Response:
    """Permanently remove a session's video, feature artifacts, and database records."""
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    result = db.query(AnalysisResult).filter(AnalysisResult.session_id == session_id).first()
    if result:
        db.delete(result)
    if session.video_path and os.path.isfile(session.video_path):
        os.remove(session.video_path)
    shutil.rmtree(os.path.join(FEATURES_DIR, session_id), ignore_errors=True)
    db.delete(session)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{session_id}/upload-video", response_model=SessionResponse)
async def upload_video(
    session_id: str,
    file: UploadFile = File(...),
    db: DBSession = Depends(get_db),
):
    """
    Accept a WebM video blob from the frontend and save it to disk.
    Updates session status to 'uploaded'.
    """
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    suffix = Path(file.filename or "recording.webm").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Upload a WebM, MP4, or MOV video")
    if file.content_type and not file.content_type.startswith("video/"):
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Uploaded file must have a video content type")
    filename = f"{session_id}{suffix}"
    file_path = os.path.join(UPLOADS_DIR, filename)

    written = 0
    try:
        async with aiofiles.open(file_path, "wb") as out_file:
            while chunk := await file.read(1024 * 1024):
                written += len(chunk)
                if written > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Video exceeds the 80 MB upload limit")
                await out_file.write(chunk)
    except HTTPException:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise
    finally:
        await file.close()
    if not written:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=422, detail="Uploaded video is empty")
    with open(file_path, "rb") as uploaded_file:
        header = uploaded_file.read(12)
    is_webm = suffix == ".webm" and header.startswith(b"\x1a\x45\xdf\xa3")
    is_iso_media = suffix in {".mp4", ".mov"} and header[4:8] == b"ftyp"
    if not (is_webm or is_iso_media):
        os.remove(file_path)
        raise HTTPException(status_code=422, detail="Uploaded video has an invalid container header")

    session.video_path = file_path
    session.status = "uploaded"
    db.commit()
    db.refresh(session)

    return session
