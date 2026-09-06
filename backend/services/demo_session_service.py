"""Generate deterministic synthetic artifacts for the public investor demo."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from services.stimulus_timeline import STIMULUS_TIMELINE, get_phase_at, get_target_at
from services.video_feature_service import FEATURES_DIR


DEMO_PHASE_ATTENTION = (0.81, 0.77, 0.74, 0.83, 0.72, 0.86)
DEMO_PHASE_ALIGNMENT = (0.84, 0.71, 0.68, 0.79, 0.65, 0.88)


def create_demo_artifacts(session_id: str) -> dict[str, Any]:
    """Create a clearly labelled synthetic result without recording or personal data."""
    output_dir = Path(FEATURES_DIR) / session_id
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamps = np.linspace(0.0, 49.75, 200)
    rows: list[dict[str, Any]] = []

    for index, timestamp in enumerate(timestamps):
        phase = get_phase_at(float(timestamp))
        target = get_target_at(float(timestamp)) or {"x": 0.5, "y": 0.5}
        gaze_x = float(np.clip(float(target["x"]) + 0.045 * np.sin(index * 0.31), 0.0, 1.0))
        gaze_y = float(np.clip(float(target["y"]) + 0.035 * np.cos(index * 0.27), 0.0, 1.0))
        tracking = float(np.clip(0.88 + 0.06 * np.sin(index * 0.13), 0.0, 1.0))
        head_motion = float(np.clip(0.08 + 0.04 * np.sin(index * 0.19), 0.0, 1.0))
        blink = 1 if index in {24, 71, 119, 166} else 0
        rows.append({
            "timestamp": round(float(timestamp), 3),
            "phase": phase.name if phase else "outside_stimulus",
            "usable_frame": 1,
            "head_motion": round(head_motion, 4),
            "blink_probability": float(blink),
            "face_detected": 1,
            "tracking_confidence": round(tracking, 4),
            "looking_away": 1 if index in {43, 44, 132} else 0,
            "gaze_screen_x": round(gaze_x, 4),
            "gaze_screen_y": round(gaze_y, 4),
            "target_screen_x": round(float(target["x"]), 4),
            "target_screen_y": round(float(target["y"]), 4),
            "target_aligned": int(abs(gaze_x - float(target["x"])) < 0.12 and abs(gaze_y - float(target["y"])) < 0.12),
        })

    phase_rows = []
    for phase, attention, alignment in zip(STIMULUS_TIMELINE, DEMO_PHASE_ATTENTION, DEMO_PHASE_ALIGNMENT):
        phase_rows.append({
            "phase": phase.name,
            "duration_sec": phase.duration_sec,
            "frame_count": 20 if phase.duration_sec == 5 else 40,
            "usable_frames": 19 if phase.duration_sec == 5 else 38,
            "attention_ratio": attention,
            "target_alignment_ratio": alignment,
            "estimated_response_latency_ms": round(460 + (1 - alignment) * 800),
            "tracking_quality": round(0.82 + alignment * 0.12, 3),
        })

    frame_df = pd.DataFrame(rows)
    heatmap, _, _ = np.histogram2d(frame_df["gaze_screen_y"], frame_df["gaze_screen_x"], bins=12, range=[[0, 1], [0, 1]])
    heatmap = heatmap / max(float(heatmap.max()), 1.0)
    gaze_path = frame_df.iloc[::2][["timestamp", "gaze_screen_x", "gaze_screen_y", "target_screen_x", "target_screen_y", "target_aligned", "phase"]].to_dict("records")
    session_features = {
        "demo_mode": True,
        "demo_data_type": "synthetic_no_personal_data",
        "attention_score": 78.0,
        "attention_level": "strong",
        "overall_usable_frames": 0.95,
        "overall_face_visibility": 0.98,
        "overall_tracking_quality": 0.91,
        "overall_gaze_stability": 0.84,
        "overall_head_stability": 0.89,
        "overall_looking_away_ratio": 0.035,
        "estimated_response_latency_ms": 565.0,
        "visualization_data": {
            "gaze_heatmap": heatmap.round(4).tolist(),
            "gaze_path": gaze_path,
            "method": "synthetic_investor_demo",
        },
        "score_breakdown": {
            "tracking_quality": 91.0,
            "face_visibility": 98.0,
            "head_stability": 89.0,
            "center_fixation": 82.0,
            "not_looking_away": 96.5,
            "gaze_stability": 84.0,
            "phase_consistency": 88.0,
            "usable_frames": 95.0,
        },
        "score_explanation": "Synthetic values for interface demonstration only.",
        "extractor_version": "synthetic_demo_v1",
        "medical_note": "synthetic_demo_not_for_clinical_use",
    }
    quality_metrics = {
        "face_visibility_ratio": 0.98,
        "usable_frames_ratio": 0.95,
        "tracking_confidence": 0.91,
        "brightness": 124.0,
        "duration": 50.0,
        "sampled_frames": len(rows),
    }

    frame_path = output_dir / "frame_features.csv"
    phase_path = output_dir / "phase_features.csv"
    session_csv_path = output_dir / "session_features.csv"
    session_json_path = output_dir / "session_features.json"
    analysis_path = output_dir / "analysis_result.json"
    frame_df.to_csv(frame_path, index=False)
    pd.DataFrame(phase_rows).to_csv(phase_path, index=False)
    pd.DataFrame([{key: value for key, value in session_features.items() if not isinstance(value, (dict, list))}]).to_csv(session_csv_path, index=False)
    session_json_path.write_text(json.dumps(session_features, ensure_ascii=False, indent=2), encoding="utf-8")
    analysis_path.write_text(json.dumps({"session_id": session_id, "demo_mode": True, "notice": "Synthetic demo data. No person was recorded."}, indent=2), encoding="utf-8")

    return {
        "feature_paths": {
            "frame_features": str(frame_path),
            "phase_features": str(phase_path),
            "session_features": str(session_csv_path),
            "session_features_json": str(session_json_path),
        },
        "session_features": session_features,
        "quality_metrics": quality_metrics,
    }
