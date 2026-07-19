"""Single-pass video → Face Mesh → frame, phase, and session feature pipeline."""

from __future__ import annotations

import json
import math
import os
from typing import Any

import cv2
import numpy as np
import pandas as pd

from services.stimulus_timeline import STIMULUS_TIMELINE, get_phase_at, get_target_at, timeline_as_dicts
from services.video_quality_service import evaluate_frame_quality
from services.vision_service import FaceMeshProcessor

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.getenv("EYEINSIGHT_DATA_DIR", BASE_DIR)
FEATURES_DIR = os.path.join(DATA_DIR, "features")
os.makedirs(FEATURES_DIR, exist_ok=True)


def _number(value: Any, default: float = 0.0) -> float:
    try:
        value = float(value)
        return value if math.isfinite(value) else default
    except (TypeError, ValueError):
        return default


def _describe(values: pd.Series) -> dict[str, float]:
    values = pd.to_numeric(values, errors="coerce").dropna()
    if values.empty:
        return {"mean": 0.0, "median": 0.0, "minimum": 0.0, "maximum": 0.0, "std": 0.0}
    return {"mean": round(_number(values.mean()), 5), "median": round(_number(values.median()), 5), "minimum": round(_number(values.min()), 5), "maximum": round(_number(values.max()), 5), "std": round(_number(values.std()), 5)}


def _read_metadata(video_path: str) -> dict[str, Any]:
    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened():
        raise ValueError("video_decode_failed")
    fps = _number(capture.get(cv2.CAP_PROP_FPS))
    reported_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width, height = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0), int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    capture.release()
    return {"fps": fps, "reported_frames": reported_frames, "width": width, "height": height}


def _frame_quality(frame: np.ndarray, mesh: dict[str, Any]) -> dict[str, Any]:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    brightness = float(gray.mean())
    contrast = float(gray.std())
    blur = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    sharpness = float(cv2.Sobel(gray, cv2.CV_64F, 1, 1).var())
    usable = int(
        mesh["face_detected"]
        and mesh["left_eye_detected"]
        and 45 <= brightness <= 220
        and blur >= 12
        and 0.025 <= mesh["face_area_ratio"] <= 0.55
        and mesh["center_offset"] <= 0.35
    )
    flags = []
    if brightness < 45: flags.append("dark")
    if blur < 12: flags.append("blurry")
    if not mesh["face_detected"]: flags.append("face_missing")
    if not mesh["left_eye_detected"]: flags.append("eyes_missing")
    if mesh["face_area_ratio"] and mesh["face_area_ratio"] < 0.025: flags.append("face_too_far")
    if mesh["face_area_ratio"] > 0.55: flags.append("face_too_close")
    return {"brightness": round(brightness, 3), "contrast": round(contrast, 3), "blur_score": round(blur, 3), "sharpness": round(sharpness, 3), "usable_frame": usable, "quality_flags": ";".join(flags)}


def _gaze_target_proxy(mesh: dict[str, Any], target: dict[str, float | str] | None) -> dict[str, Any]:
    gaze_x, gaze_y = _number(mesh.get("gaze_x"), float("nan")), _number(mesh.get("gaze_y"), float("nan"))
    if target is None or not math.isfinite(gaze_x) or not math.isfinite(gaze_y):
        return {"gaze_screen_x": np.nan, "gaze_screen_y": np.nan, "target_screen_x": np.nan, "target_screen_y": np.nan, "target_zone": "none", "gaze_target_distance": np.nan, "target_aligned": 0}
    screen_x = float(np.clip(0.5 + gaze_x * 0.5, 0.0, 1.0))
    screen_y = float(np.clip(0.5 + gaze_y * 0.5, 0.0, 1.0))
    target_x, target_y = float(target["x"]), float(target["y"])
    distance = float(math.hypot(screen_x - target_x, screen_y - target_y))
    aligned = int(mesh["tracking_confidence"] >= 0.45 and distance <= 0.30)
    return {"gaze_screen_x": round(screen_x, 5), "gaze_screen_y": round(screen_y, 5), "target_screen_x": round(target_x, 5), "target_screen_y": round(target_y, 5), "target_zone": str(target["zone"]), "gaze_target_distance": round(distance, 5), "target_aligned": aligned}


def extract_video_features(video_path: str, session_id: str, output_dir: str | None = None) -> dict[str, Any]:
    """Process every decodable frame once and persist all pipeline artifacts."""
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    metadata = _read_metadata(video_path)
    output_dir = output_dir or os.path.join(FEATURES_DIR, session_id)
    os.makedirs(output_dir, exist_ok=True)
    rows: list[dict[str, Any]] = []
    capture = cv2.VideoCapture(video_path)
    frame_index, decoded = 0, 0
    with FaceMeshProcessor() as processor:
        while True:
            ok, frame = capture.read()
            if not ok or frame is None:
                break
            decoded += 1
            timestamp = frame_index / metadata["fps"] if metadata["fps"] > 0 else float(frame_index)
            phase = get_phase_at(timestamp)
            mesh = processor.process(frame, timestamp)
            quality = _frame_quality(frame, mesh)
            gaze_target = _gaze_target_proxy(mesh, get_target_at(timestamp))
            rows.append({
                "session_id": session_id,
                "timestamp": round(timestamp, 4),
                "timestamp_sec": round(timestamp, 4),
                "frame_index": frame_index,
                "phase": phase.name if phase else "outside_stimulus",
                "phase_name": phase.name if phase else "outside_stimulus",
                "stimulus_type": phase.stimulus_type if phase else "none",
                **mesh,
                **quality,
                **gaze_target,
            })
            frame_index += 1
    capture.release()
    if not rows:
        raise ValueError("video_decode_failed")
    frame_df = pd.DataFrame(rows)
    duration = frame_df["timestamp"].iloc[-1] if metadata["fps"] > 0 else float(len(frame_df))
    expected = int(round(metadata["fps"] * duration)) if metadata["fps"] > 0 else decoded
    quality_assessment = evaluate_frame_quality(frame_df, metadata["fps"], duration, decoded, expected)
    frame_df["quality_score"] = quality_assessment["quality_score"]
    frame_path = os.path.join(output_dir, "frame_features.csv")
    frame_df.to_csv(frame_path, index=False)
    phase_df = _aggregate_phases(session_id, frame_df)
    session_features = _aggregate_session(session_id, frame_df, phase_df, duration, metadata, quality_assessment)
    phase_path = os.path.join(output_dir, "phase_features.csv")
    session_csv_path = os.path.join(output_dir, "session_features.csv")
    session_json_path = os.path.join(output_dir, "session_features.json")
    timeline_path = os.path.join(output_dir, "stimulus_timeline.json")
    phase_df.to_csv(phase_path, index=False)
    pd.DataFrame([session_features]).to_csv(session_csv_path, index=False)
    with open(session_json_path, "w", encoding="utf-8") as handle:
        json.dump(session_features, handle, ensure_ascii=False, indent=2)
    with open(timeline_path, "w", encoding="utf-8") as handle:
        json.dump(timeline_as_dicts(), handle, ensure_ascii=False, indent=2)
    return {"session_id": session_id, "output_dir": output_dir, "frame_features_path": frame_path, "phase_features_path": phase_path, "session_features_path": session_csv_path, "session_features_json_path": session_json_path, "stimulus_timeline_path": timeline_path, "quality": quality_assessment, "session_features": session_features}


def _aggregate_phases(session_id: str, frame_df: pd.DataFrame) -> pd.DataFrame:
    phase_rows: list[dict[str, Any]] = []
    for phase in STIMULUS_TIMELINE:
        frames = frame_df.loc[frame_df["phase"] == phase.name].copy()
        total = len(frames)
        if not total:
            phase_rows.append({"session_id": session_id, "phase": phase.name, "duration_sec": phase.duration_sec, "usable_frames": 0, "frame_count": 0, "attention_ratio": 0.0, "target_alignment_ratio": 0.0, "estimated_response_latency_ms": None, "tracking_quality": 0.0, "center_fixation": 0.0, "head_stability": 0.0, "head_movement": 0.0, "blink_count": 0, "blink_rate": 0.0, "looking_away_ratio": 1.0, "gaze_stability": 0.0, "reaction_latency_sec": None})
            continue
        gaze_distance = np.sqrt(frames["gaze_x"].diff().fillna(0) ** 2 + frames["gaze_y"].diff().fillna(0) ** 2)
        away = frames["looking_direction"].isin(["looking_away", "tracking_lost"])
        attention = frames["usable_frame"] * (~away).astype(int)
        first_attended = frames.loc[attention.astype(bool), "timestamp"].min()
        aligned = frames["target_aligned"] == 1
        first_aligned = frames.loc[aligned, "timestamp"].min()
        row: dict[str, Any] = {"session_id": session_id, "phase": phase.name, "duration_sec": phase.duration_sec, "frame_count": total, "usable_frames": int(frames["usable_frame"].sum()), "attention_ratio": round(_number(attention.mean()), 5), "target_alignment_ratio": round(_number(aligned.mean()), 5), "estimated_response_latency_ms": round(_number((first_aligned - phase.start_sec) * 1000), 1) if pd.notna(first_aligned) else None, "tracking_quality": round(_number(frames["tracking_confidence"].mean()), 5), "center_fixation": round(_number((frames["center_offset"] <= 0.20).mean()), 5), "head_stability": round(_number(frames["head_stability"].mean()), 5), "head_movement": round(_number(frames["head_motion"].mean()), 5), "blink_count": int(frames["blink"].sum()), "blink_rate": round(float(frames["blink"].sum()) / max(phase.duration_sec, 1) * 60, 3), "looking_away_ratio": round(_number(away.mean()), 5), "gaze_stability": round(float(np.clip(1 - gaze_distance.mean() * 4, 0, 1)), 5), "reaction_latency_sec": round(_number(first_attended - phase.start_sec), 4) if pd.notna(first_attended) else None}
        for feature in ("tracking_confidence", "head_stability", "head_motion", "gaze_x", "gaze_y", "face_area_ratio"):
            for stat, value in _describe(frames[feature]).items():
                row[f"{feature}_{stat}"] = value
        phase_rows.append(row)
    return pd.DataFrame(phase_rows)


def _aggregate_session(session_id: str, frame_df: pd.DataFrame, phase_df: pd.DataFrame, duration: float, metadata: dict[str, Any], quality: dict[str, Any]) -> dict[str, Any]:
    in_task = frame_df[frame_df["phase"] != "outside_stimulus"].copy()
    source = in_task if not in_task.empty else frame_df
    away = source["looking_direction"].isin(["looking_away", "tracking_lost"])
    gaze_delta = np.sqrt(source["gaze_x"].diff().fillna(0) ** 2 + source["gaze_y"].diff().fillna(0) ** 2)
    phase_consistency = float(np.clip(1 - phase_df["attention_ratio"].std(ddof=0), 0, 1)) if len(phase_df) else 0.0
    attention_components = {"tracking_quality": _number(source["tracking_confidence"].mean()), "face_visibility": _number(source["face_detected"].mean()), "head_stability": _number(source["head_stability"].mean()), "center_fixation": _number((source["center_offset"] <= 0.20).mean()), "not_looking_away": 1 - _number(away.mean(), 1), "gaze_stability": float(np.clip(1 - gaze_delta.mean() * 4, 0, 1)), "phase_consistency": phase_consistency, "usable_frames": _number(source["usable_frame"].mean())}
    weights = {"tracking_quality": .18, "face_visibility": .14, "head_stability": .14, "center_fixation": .14, "not_looking_away": .14, "gaze_stability": .10, "phase_consistency": .08, "usable_frames": .08}
    attention_score = round(100 * sum(attention_components[key] * weight for key, weight in weights.items()), 1)
    if attention_score >= 75: attention_level = "strong"
    elif attention_score >= 50: attention_level = "mixed"
    else: attention_level = "limited"
    reaction_values = phase_df["reaction_latency_sec"].dropna() if "reaction_latency_sec" in phase_df else pd.Series(dtype=float)
    response_values = phase_df["estimated_response_latency_ms"].dropna() if "estimated_response_latency_ms" in phase_df else pd.Series(dtype=float)
    estimated_response_latency = round(float(response_values.mean()), 1) if not response_values.empty else None
    features: dict[str, Any] = {"session_id": session_id, "session_duration_sec": round(float(duration), 3), "fps": round(metadata["fps"], 3), "total_frames": int(len(frame_df)), "overall_attention": attention_score, "attention_score": attention_score, "attention_level": attention_level, "overall_tracking_quality": round(attention_components["tracking_quality"], 5), "overall_gaze_stability": round(attention_components["gaze_stability"], 5), "overall_head_stability": round(attention_components["head_stability"], 5), "overall_blink_rate": round(float(source["blink"].sum()) / max(duration, 1) * 60, 3), "overall_face_visibility": round(attention_components["face_visibility"], 5), "overall_eyes_visibility": round(_number(((source["left_eye_detected"] + source["right_eye_detected"]) > 0).mean()), 5), "overall_usable_frames": round(attention_components["usable_frames"], 5), "overall_quality_score": quality["quality_score"], "overall_looking_away_ratio": round(_number(away.mean()), 5), "overall_center_fixation": round(attention_components["center_fixation"], 5), "overall_target_alignment_proxy": round(_number(source["target_aligned"].mean()), 5), "estimated_response_latency_ms": estimated_response_latency, "head_movement_mean": round(_number(source["head_motion"].mean()), 5), "reaction_latency_mean_sec": round(_number(reaction_values.mean()), 4), "reaction_latency_std_sec": round(_number(reaction_values.std()), 4), "quality_metrics": quality["metrics"], "quality_fail_reasons": quality["issues"], "visualization_data": _visualization_data(source), "score_breakdown": {key: round(value * 100, 1) for key, value in attention_components.items()}, "score_explanation": "Weighted technical attention indicators: tracking, face visibility, head and gaze stability, center fixation, phase consistency, and usable frames.", "extractor_version": "mediapipe_face_mesh_v3_stimulus_proxy", "medical_note": "screening_support_only_not_diagnostic"}
    for _, row in phase_df.iterrows():
        prefix = str(row["phase"])
        features[f"{prefix}_attention_ratio"] = _number(row["attention_ratio"])
        features[f"{prefix}_looking_away_ratio"] = _number(row["looking_away_ratio"])
    return features


def _visualization_data(frame_df: pd.DataFrame, bins: int = 12, max_points: int = 240) -> dict[str, Any]:
    valid = frame_df.dropna(subset=["gaze_screen_x", "gaze_screen_y"])
    if valid.empty:
        return {"gaze_heatmap": [], "gaze_path": [], "method": "uncalibrated_gaze_proxy"}
    heatmap, _, _ = np.histogram2d(valid["gaze_screen_y"], valid["gaze_screen_x"], bins=bins, range=[[0, 1], [0, 1]])
    maximum = float(heatmap.max())
    normalized = (heatmap / maximum).round(4).tolist() if maximum else heatmap.tolist()
    indices = np.linspace(0, len(valid) - 1, min(max_points, len(valid))).astype(int)
    path = valid.iloc[indices][["timestamp", "gaze_screen_x", "gaze_screen_y", "target_screen_x", "target_screen_y", "target_aligned", "phase"]].replace({np.nan: None}).to_dict("records")
    return {"gaze_heatmap": normalized, "gaze_path": path, "method": "uncalibrated_gaze_proxy"}
