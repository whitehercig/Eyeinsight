"""Analysis, feature-inspection, and artifact-download routes."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pandas as pd
import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session as DBSession

from database import get_db
from models import AnalysisResult, Session
from schemas import AnalysisResultResponse, FeatureBundleResponse
from services.risk_model_service import score_from_session_features
from services.video_feature_service import FEATURES_DIR, extract_video_features

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analyze-session/{session_id}", response_model=AnalysisResultResponse)
def analyze_session(session_id: str, db: DBSession = Depends(get_db)) -> dict[str, Any]:
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status not in {"uploaded", "analyzed", "quality_failed"}:
        raise HTTPException(status_code=409, detail=f"Session is not ready for analysis (status: {session.status})")
    if not session.video_path:
        raise HTTPException(status_code=422, detail="No video is attached to this session")
    try:
        feature_output = extract_video_features(session.video_path, session_id=session_id)
    except (FileNotFoundError, ValueError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Video processing failed. Confirm MediaPipe is installed and the uploaded video is readable.") from error

    existing = db.query(AnalysisResult).filter(AnalysisResult.session_id == session_id).first()
    if existing:
        db.delete(existing)
        db.flush()
    quality = feature_output["quality"]
    session_features = feature_output["session_features"]
    feature_paths = {key.replace("_path", ""): value for key, value in feature_output.items() if key.endswith("_path")}
    if quality["passed"]:
        inference = score_from_session_features(session_features)
        result = AnalysisResult(session_id=session_id, risk_score=inference["risk_score"], risk_level=inference["risk_level"], quality_score=quality["quality_score"], quality_failed=False, quality_issues=json.dumps(quality["issues"]), quality_metrics=json.dumps(quality["metrics"]), feature_paths=json.dumps(feature_paths), session_features_json=json.dumps(session_features), model_version=inference["model_version"], model_explanation=json.dumps(inference), summary_code=inference["summary_code"], recommendation_codes=json.dumps(inference["recommendation_codes"]))
        session.status = "analyzed"
    else:
        result = AnalysisResult(session_id=session_id, risk_score=None, risk_level=None, quality_score=quality["quality_score"], quality_failed=True, quality_issues=json.dumps(quality["issues"]), quality_metrics=json.dumps(quality["metrics"]), feature_paths=json.dumps(feature_paths), session_features_json=json.dumps(session_features), model_version="quality_gate_v2", model_explanation=json.dumps({"medical_disclaimer": "No behavioral screening indicator is generated when video quality does not pass."}), summary_code="quality_failed_summary", recommendation_codes=json.dumps(["not_diagnosis", "repeat_if_low_quality"]))
        session.status = "quality_failed"
    db.add(result)
    db.commit()
    db.refresh(result)
    report_path = Path(feature_output["output_dir"]) / "analysis_result.json"
    report_path.write_text(json.dumps(_serialize(result), default=str, ensure_ascii=False, indent=2), encoding="utf-8")
    return _serialize(result)


@router.get("/sessions/{session_id}/result", response_model=AnalysisResultResponse)
def get_result(session_id: str, db: DBSession = Depends(get_db)) -> dict[str, Any]:
    result = _result_or_404(session_id, db)
    return _serialize(result)


@router.get("/sessions/{session_id}/features", response_model=FeatureBundleResponse)
def get_features(session_id: str, db: DBSession = Depends(get_db)) -> dict[str, Any]:
    result = _result_or_404(session_id, db)
    paths = json.loads(result.feature_paths or "{}")
    phase_features = _read_csv(paths.get("phase_features"))
    frame_preview = _read_csv(paths.get("frame_features"), 180)
    session_features = json.loads(result.session_features_json or "{}")
    explanation = json.loads(result.model_explanation or "{}")
    downloads = {name: f"/api/sessions/{session_id}/downloads/{name}" for name in ("frame_features.csv", "phase_features.csv", "session_features.csv", "session_features.json", "analysis_result.json")}
    return {"session_id": session_id, "quality_metrics": json.loads(result.quality_metrics or "{}"), "frame_preview": frame_preview, "frame_features": frame_preview, "phase_features": phase_features, "session_features": session_features, "attention_score": session_features.get("attention_score"), "attention_level": session_features.get("attention_level"), "risk_score": result.risk_score, "risk_level": result.risk_level, "risk_details": explanation, "downloads": downloads, "medical_disclaimer": "EyeInsight is an AI-assisted behavioral screening support tool. It does not diagnose any condition."}


@router.get("/sessions/{session_id}/downloads/{filename}")
def download_artifact(session_id: str, filename: str, db: DBSession = Depends(get_db)) -> FileResponse:
    _result_or_404(session_id, db)
    allowed = {"frame_features.csv", "phase_features.csv", "session_features.csv", "session_features.json", "analysis_result.json"}
    if filename not in allowed:
        raise HTTPException(status_code=404, detail="Artifact not found")
    path = Path(FEATURES_DIR) / session_id / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Artifact has not been generated")
    media_type = "text/csv" if path.suffix == ".csv" else "application/json"
    return FileResponse(path, media_type=media_type, filename=filename)


def _result_or_404(session_id: str, db: DBSession) -> AnalysisResult:
    result = db.query(AnalysisResult).filter(AnalysisResult.session_id == session_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="No analysis result for this session")
    return result


def _read_csv(path: str | None, limit: int | None = None) -> list[dict[str, Any]]:
    if not path or not os.path.isfile(path):
        return []
    frame = pd.read_csv(path, nrows=limit)
    frame = frame.replace({np.nan: None})
    return frame.to_dict("records")


def _serialize(result: AnalysisResult) -> dict[str, Any]:
    explanation = json.loads(result.model_explanation or "{}")
    session_features = json.loads(result.session_features_json or "{}")
    return {"session_id": result.session_id, "risk_score": result.risk_score, "risk_level": result.risk_level, "quality_score": result.quality_score, "quality_failed": result.quality_failed, "quality_issues": json.loads(result.quality_issues or "[]"), "quality_metrics": json.loads(result.quality_metrics or "{}"), "feature_summary": {key: session_features.get(key) for key in ("attention_score", "attention_level", "overall_tracking_quality", "overall_face_visibility", "overall_gaze_stability", "overall_head_stability", "overall_looking_away_ratio", "overall_usable_frames")}, "attention_score": session_features.get("attention_score"), "attention_level": session_features.get("attention_level"), "score_breakdown": session_features.get("score_breakdown", {}), "score_explanation": session_features.get("score_explanation"), "risk_confidence": explanation.get("confidence"), "risk_confidence_type": explanation.get("confidence_type"), "top_contributing_factors": explanation.get("top_contributing_factors", []), "model_version": result.model_version, "summary_code": result.summary_code, "recommendation_codes": json.loads(result.recommendation_codes or "[]"), "created_at": result.created_at}
