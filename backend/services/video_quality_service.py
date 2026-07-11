"""Technical video quality scoring derived from every processed frame."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def evaluate_frame_quality(frame_df: pd.DataFrame, fps: float, duration: float, decoded_frames: int, expected_frames: int) -> dict[str, Any]:
    if frame_df.empty:
        return _result(0.0, False, ["video_decode_failed"], {"sampled_frames": 0})
    numeric_mean = lambda column: float(frame_df[column].fillna(0).mean())
    face_ratio = numeric_mean("face_detected")
    eyes_ratio = ((frame_df["left_eye_detected"] + frame_df["right_eye_detected"]) > 0).mean()
    centered_ratio = (frame_df["center_offset"].fillna(1.0) <= 0.30).mean()
    usable = frame_df["usable_frame"].mean()
    brightness, contrast = numeric_mean("brightness"), numeric_mean("contrast")
    blur, sharpness = numeric_mean("blur_score"), numeric_mean("sharpness")
    face_area = numeric_mean("face_area_ratio")
    tracking = numeric_mean("tracking_confidence")
    drop_ratio = max(0.0, 1.0 - decoded_frames / max(1, expected_frames)) if fps > 0 else 0.0
    normalized = lambda value, low, high: float(np.clip((value - low) / max(1e-6, high - low), 0.0, 1.0))
    score = 100 * (0.22 * usable + 0.18 * face_ratio + 0.10 * eyes_ratio + 0.10 * centered_ratio + 0.10 * normalized(brightness, 45, 115) + 0.10 * normalized(blur, 12, 100) + 0.10 * tracking + 0.10 * (1 - drop_ratio))
    issues: list[str] = []
    if duration < 10: issues.append("video_too_short")
    if fps < 12: issues.append("fps_too_low")
    if brightness < 45: issues.append("lighting_low")
    if blur < 12: issues.append("video_blurry")
    if face_ratio < 0.55: issues.append("face_not_visible")
    if eyes_ratio < 0.45: issues.append("eyes_not_visible")
    if face_area < 0.025: issues.append("face_too_far")
    if face_area > 0.55: issues.append("face_too_close")
    if usable < 0.50: issues.append("insufficient_usable_frames")
    passed = not any(issue in issues for issue in ("video_too_short", "fps_too_low", "lighting_low", "video_blurry", "face_not_visible", "eyes_not_visible", "face_too_far", "face_too_close", "insufficient_usable_frames")) and score >= 55
    metrics = {"face_detected": round(face_ratio, 4), "face_visibility_ratio": round(face_ratio, 4), "usable_frames_ratio": round(float(usable), 4), "brightness": round(brightness, 2), "contrast": round(contrast, 2), "blur_score": round(blur, 2), "sharpness": round(sharpness, 2), "fps": round(fps, 2), "duration": round(duration, 2), "frame_drop_ratio": round(drop_ratio, 4), "eyes_detected_ratio": round(float(eyes_ratio), 4), "face_center_ratio": round(float(centered_ratio), 4), "face_area_ratio": round(face_area, 4), "distance_proxy": round(numeric_mean("distance_proxy"), 4), "tracking_confidence": round(tracking, 4), "head_visibility": round(face_ratio, 4), "sampled_frames": int(len(frame_df))}
    return _result(round(float(score), 1), passed, issues, metrics)


def _result(score: float, passed: bool, issues: list[str], metrics: dict[str, Any]) -> dict[str, Any]:
    return {"quality_score": score, "passed": bool(passed), "issues": issues, "metrics": metrics}
