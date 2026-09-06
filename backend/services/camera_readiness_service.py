"""Pre-recording camera readiness checks using a short burst of still frames."""

from __future__ import annotations

from typing import Any

import cv2
import numpy as np

from services.vision_service import FaceMeshProcessor


MIN_BRIGHTNESS = 55.0
MAX_BRIGHTNESS = 215.0
MIN_FACE_AREA = 0.04
MAX_FACE_AREA = 0.34
MAX_CENTER_OFFSET = 0.24
MIN_STABILITY = 0.68


def assess_camera_frames(frames: list[np.ndarray]) -> dict[str, Any]:
    """Return blocking readiness checks for lighting, framing, distance, and stability."""
    observations: list[dict[str, Any]] = []
    with FaceMeshProcessor() as processor:
        for index, frame in enumerate(frames):
            analysis_frame = _resize(frame)
            mesh = processor.process(analysis_frame, index * 0.25)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            observations.append({
                **mesh,
                "brightness": float(gray.mean()),
            })
    return summarize_camera_observations(observations)


def summarize_camera_observations(observations: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize observations separately so thresholds remain unit-testable."""
    if len(observations) < 3:
        raise ValueError("camera_check_needs_more_frames")

    brightness = float(np.mean([float(item.get("brightness", 0.0)) for item in observations]))
    detected = [item for item in observations if int(item.get("face_detected", 0)) == 1]
    face_ratio = len(detected) / len(observations)
    face_area = float(np.median([float(item.get("face_area_ratio", 0.0)) for item in detected])) if detected else 0.0
    center_offset = float(np.median([float(item.get("center_offset", 1.0)) for item in detected])) if detected else 1.0
    stable_values = [float(item.get("head_stability", 0.0)) for item in detected[1:]]
    stability = float(np.mean(stable_values)) if stable_values else 0.0

    lighting_ok = MIN_BRIGHTNESS <= brightness <= MAX_BRIGHTNESS
    face_visible = face_ratio >= 0.75
    face_centered = face_visible and center_offset <= MAX_CENTER_OFFSET
    distance_ok = face_visible and MIN_FACE_AREA <= face_area <= MAX_FACE_AREA
    stability_ok = face_visible and stability >= MIN_STABILITY

    issues: list[str] = []
    if brightness < MIN_BRIGHTNESS:
        issues.append("lighting_low")
    elif brightness > MAX_BRIGHTNESS:
        issues.append("lighting_high")
    if not face_visible:
        issues.append("face_not_visible")
    elif not face_centered:
        issues.append("face_not_centered")
    if face_visible and face_area < MIN_FACE_AREA:
        issues.append("face_too_far")
    elif face_visible and face_area > MAX_FACE_AREA:
        issues.append("face_too_close")
    if face_visible and not stability_ok:
        issues.append("camera_unstable")

    checks = {
        "lighting": lighting_ok,
        "face_in_frame": face_visible and face_centered,
        "distance": distance_ok,
        "stability": stability_ok,
    }
    return {
        "ready": all(checks.values()),
        "checks": checks,
        "issues": issues,
        "metrics": {
            "brightness": round(brightness, 1),
            "face_visibility": round(face_ratio, 3),
            "face_area_ratio": round(face_area, 4),
            "center_offset": round(center_offset, 4),
            "head_stability": round(stability, 3),
        },
    }


def _resize(frame: np.ndarray, target_width: int = 320) -> np.ndarray:
    if frame.shape[1] <= target_width:
        return frame
    height = max(1, round(frame.shape[0] * target_width / frame.shape[1]))
    return cv2.resize(frame, (target_width, height), interpolation=cv2.INTER_AREA)
