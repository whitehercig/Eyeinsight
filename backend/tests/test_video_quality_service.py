import pandas as pd

from services.video_quality_service import evaluate_frame_quality


def _frame_rows(count: int, **overrides: float) -> pd.DataFrame:
    row = {"face_detected": 1, "left_eye_detected": 1, "right_eye_detected": 1, "usable_frame": 1, "brightness": 100, "contrast": 30, "blur_score": 100, "sharpness": 90, "center_offset": .1, "face_area_ratio": .2, "distance_proxy": 1, "tracking_confidence": .9}
    row.update(overrides)
    return pd.DataFrame([row] * count)


def test_quality_passes_usable_well_lit_video() -> None:
    quality = evaluate_frame_quality(_frame_rows(180), fps=15, duration=12, decoded_frames=180, expected_frames=180)

    assert quality["passed"] is True
    assert quality["quality_score"] >= 55
    assert quality["issues"] == []


def test_quality_rejects_missing_face_and_dark_video() -> None:
    quality = evaluate_frame_quality(_frame_rows(30, face_detected=0, left_eye_detected=0, right_eye_detected=0, usable_frame=0, brightness=15), fps=15, duration=12, decoded_frames=30, expected_frames=180)

    assert quality["passed"] is False
    assert {"lighting_low", "face_not_visible", "eyes_not_visible", "insufficient_usable_frames"}.issubset(quality["issues"])
