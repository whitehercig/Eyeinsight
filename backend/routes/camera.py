"""Camera readiness endpoint used before a recording starts."""

from __future__ import annotations

import cv2
import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile, status

from schemas import CameraReadinessResponse
from services.camera_readiness_service import assess_camera_frames


router = APIRouter(prefix="/api", tags=["camera"])
MAX_FRAME_BYTES = 1_500_000
MIN_FRAMES = 3
MAX_FRAMES = 6


@router.post("/camera-check", response_model=CameraReadinessResponse)
async def camera_check(files: list[UploadFile] = File(...)) -> dict:
    if not MIN_FRAMES <= len(files) <= MAX_FRAMES:
        raise HTTPException(status_code=422, detail="camera_check_needs_3_to_6_frames")

    frames = []
    for upload in files:
        if upload.content_type and not upload.content_type.startswith("image/"):
            raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="camera_frame_must_be_an_image")
        payload = await upload.read(MAX_FRAME_BYTES + 1)
        await upload.close()
        if not payload or len(payload) > MAX_FRAME_BYTES:
            raise HTTPException(status_code=422, detail="camera_frame_invalid")
        frame = cv2.imdecode(np.frombuffer(payload, dtype=np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            raise HTTPException(status_code=422, detail="camera_frame_invalid")
        frames.append(frame)

    try:
        return assess_camera_frames(frames)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="camera_check_failed") from error
