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
from services.report_service import create_session_report
from services.video_feature_service import FEATURES_DIR, extract_video_features

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analyze-session/{session_id}", response_model=AnalysisResultResponse)
def analyze_session(session_id: str, retry: bool = False, db: DBSession = Depends(get_db)) -> dict[str, Any]:
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    existing = db.query(AnalysisResult).filter(AnalysisResult.session_id == session_id).first()
    if existing and session.status in {"analyzed", "quality_failed"}:
        _delete_source_video(session, db)
        return _serialize(existing)
    if session.status == "processing" and not retry:
        raise HTTPException(status_code=409, detail="analysis_in_progress")
    if session.status not in {"uploaded", "analysis_failed", "processing"}:
        raise HTTPException(status_code=409, detail=f"Session is not ready for analysis (status: {session.status})")
    if not session.video_path:
        raise HTTPException(status_code=422, detail="No video is attached to this session")
    session.status = "processing"
    db.commit()
    try:
        feature_output = extract_video_features(session.video_path, session_id=session_id)
    except (FileNotFoundError, ValueError) as error:
        _mark_analysis_failed(session, db)
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        _mark_analysis_failed(session, db)
        raise HTTPException(status_code=500, detail="Video processing failed. Confirm MediaPipe is installed and the uploaded video is readable.") from error

    if existing:
        db.delete(existing)
        db.flush()
    quality = feature_output["quality"]
    session_features = feature_output["session_features"]
    feature_paths = {key.replace("_path", ""): value for key, value in feature_output.items() if key.endswith("_path")}
    if quality["passed"]:
        pipeline_details = {
            "pipeline": session_features.get("extractor_version", "computer_vision_feature_pipeline"),
            "validation_status": "research_prototype_not_clinically_validated",
            "output_type": "descriptive_technical_metrics_only",
        }
        result = AnalysisResult(session_id=session_id, risk_score=None, risk_level=None, quality_score=quality["quality_score"], quality_failed=False, quality_issues=json.dumps(quality["issues"]), quality_metrics=json.dumps(quality["metrics"]), feature_paths=json.dumps(feature_paths), session_features_json=json.dumps(session_features), model_version=session_features.get("extractor_version"), model_explanation=json.dumps(pipeline_details), summary_code="technical_session_complete", recommendation_codes=json.dumps(["not_diagnosis"]))
        session.status = "analyzed"
    else:
        result = AnalysisResult(session_id=session_id, risk_score=None, risk_level=None, quality_score=quality["quality_score"], quality_failed=True, quality_issues=json.dumps(quality["issues"]), quality_metrics=json.dumps(quality["metrics"]), feature_paths=json.dumps(feature_paths), session_features_json=json.dumps(session_features), model_version="quality_gate_v2", model_explanation=json.dumps({"medical_disclaimer": "No behavioral screening indicator is generated when video quality does not pass."}), summary_code="quality_failed_summary", recommendation_codes=json.dumps(["not_diagnosis", "repeat_if_low_quality"]))
        session.status = "quality_failed"
    db.add(result)
    db.commit()
    db.refresh(result)
    _delete_source_video(session, db)
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
    frame_preview = _read_csv(paths.get("frame_features"), 240, sample=True)
    session_features = json.loads(result.session_features_json or "{}")
    explanation = json.loads(result.model_explanation or "{}")
    downloads = {name: f"/api/sessions/{session_id}/downloads/{name}" for name in ("frame_features.csv", "phase_features.csv", "session_features.csv", "session_features.json", "analysis_result.json")}
    return {"session_id": session_id, "quality_metrics": json.loads(result.quality_metrics or "{}"), "frame_preview": frame_preview, "frame_features": frame_preview, "phase_features": phase_features, "session_features": session_features, "attention_score": session_features.get("attention_score"), "attention_level": session_features.get("attention_level"), "risk_score": None, "risk_level": None, "risk_details": explanation, "visualizations": session_features.get("visualization_data", {}), "downloads": downloads, "medical_disclaimer": "EyeInsight provides descriptive technical metrics from an unvalidated research prototype. It does not generate a diagnosis or clinical risk estimate."}


@router.get("/sessions/{session_id}/clinical-report")
def clinical_report(session_id: str, lang: str = "ru", db: DBSession = Depends(get_db)) -> FileResponse:
    if lang not in {"en", "ru", "kz"}:
        raise HTTPException(status_code=422, detail="Supported report languages: en, ru, kz")
    result = _result_or_404(session_id, db)
    paths = json.loads(result.feature_paths or "{}")
    phase_features = _read_csv(paths.get("phase_features"))
    session_features = json.loads(result.session_features_json or "{}")
    output_path = Path(FEATURES_DIR) / session_id / f"session_report_{lang}.pdf"
    create_session_report(output_path, session_id, _serialize(result), session_features, phase_features, lang)
    return FileResponse(output_path, media_type="application/pdf", filename=f"eyeinsight_session_report_{session_id[:8]}.pdf")


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


def _read_csv(path: str | None, limit: int | None = None, sample: bool = False) -> list[dict[str, Any]]:
    if not path or not os.path.isfile(path):
        return []
    frame = pd.read_csv(path)
    if limit and len(frame) > limit:
        frame = frame.iloc[np.linspace(0, len(frame) - 1, limit).astype(int)] if sample else frame.head(limit)
    frame = frame.replace({np.nan: None})
    return frame.to_dict("records")


def _serialize(result: AnalysisResult) -> dict[str, Any]:
    explanation = json.loads(result.model_explanation or "{}")
    session_features = json.loads(result.session_features_json or "{}")
    source_video_path = getattr(getattr(result, "session", None), "video_path", None)
    return {"session_id": result.session_id, "risk_score": result.risk_score, "risk_level": result.risk_level, "quality_score": result.quality_score, "quality_failed": result.quality_failed, "quality_issues": json.loads(result.quality_issues or "[]"), "quality_metrics": json.loads(result.quality_metrics or "{}"), "feature_summary": {key: session_features.get(key) for key in ("attention_score", "attention_level", "overall_tracking_quality", "overall_face_visibility", "overall_gaze_stability", "overall_head_stability", "overall_looking_away_ratio", "overall_usable_frames")}, "attention_score": session_features.get("attention_score"), "attention_level": session_features.get("attention_level"), "score_breakdown": session_features.get("score_breakdown", {}), "score_explanation": session_features.get("score_explanation"), "risk_confidence": explanation.get("confidence"), "risk_confidence_type": explanation.get("confidence_type"), "top_contributing_factors": explanation.get("top_contributing_factors", []), "model_version": result.model_version, "summary_code": result.summary_code, "recommendation_codes": json.loads(result.recommendation_codes or "[]"), "source_video_deleted": not bool(source_video_path), "is_demo": bool(session_features.get("demo_mode")), "created_at": result.created_at}


def _mark_analysis_failed(session: Session, db: DBSession) -> None:
    session.status = "analysis_failed"
    db.commit()


def _delete_source_video(session: Session, db: DBSession) -> None:
    """Delete raw video after feature extraction unless explicitly disabled."""
    should_delete = os.getenv("EYEINSIGHT_DELETE_SOURCE_VIDEO", "true").lower() not in {"0", "false", "no"}
    if not should_delete or not session.video_path:
        return
    Path(session.video_path).unlink(missing_ok=True)
    session.video_path = None
    db.commit()
