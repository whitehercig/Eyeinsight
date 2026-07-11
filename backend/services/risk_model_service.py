"""Transparent, non-diagnostic rule-based screening indicator model."""

from __future__ import annotations

from typing import Any


def _bounded(value: Any, default: float = 0.0) -> float:
    try:
        return min(1.0, max(0.0, float(value)))
    except (TypeError, ValueError):
        return default


def score_from_session_features(session_features: dict[str, Any]) -> dict[str, Any]:
    """Return a deterministic behavioral screening indicator, never a diagnosis."""
    components = {
        "low_attention_pattern": 1 - _bounded(session_features.get("attention_score", 0) / 100),
        "limited_tracking": 1 - _bounded(session_features.get("overall_tracking_quality")),
        "face_visibility": 1 - _bounded(session_features.get("overall_face_visibility")),
        "looking_away": _bounded(session_features.get("overall_looking_away_ratio"), 1),
        "limited_center_fixation": 1 - _bounded(session_features.get("overall_center_fixation")),
        "head_instability": 1 - _bounded(session_features.get("overall_head_stability")),
        "gaze_instability": 1 - _bounded(session_features.get("overall_gaze_stability")),
    }
    weights = {"low_attention_pattern": .25, "limited_tracking": .15, "face_visibility": .10, "looking_away": .18, "limited_center_fixation": .12, "head_instability": .10, "gaze_instability": .10}
    contributions = {name: round(value * weights[name] * 100, 2) for name, value in components.items()}
    risk_score = round(sum(contributions.values()), 1)
    if risk_score < 35:
        risk_level, summary_code = "low", "low_risk_summary"
        recommendations = ["not_diagnosis", "consult_specialist_if_concerned", "continue_routine_checkups"]
    elif risk_score < 65:
        risk_level, summary_code = "moderate", "moderate_risk_summary"
        recommendations = ["not_diagnosis", "consult_specialist", "repeat_if_low_quality"]
    else:
        risk_level, summary_code = "elevated", "elevated_risk_summary"
        recommendations = ["not_diagnosis", "consult_specialist", "repeat_if_low_quality"]
    input_coverage = sum(_bounded(session_features.get(key)) for key in ("overall_tracking_quality", "overall_face_visibility", "overall_usable_frames")) / 3
    quality = _bounded(session_features.get("overall_quality_score", 0) / 100)
    confidence = round(100 * (0.65 * quality + 0.35 * input_coverage), 1)
    top_factors = [{"factor": name, "contribution": value} for name, value in sorted(contributions.items(), key=lambda item: item[1], reverse=True)[:3] if value > 0]
    return {"risk_score": risk_score, "risk_level": risk_level, "confidence": confidence, "confidence_type": "technical_input_reliability_not_clinical_probability", "top_contributing_factors": top_factors, "summary_code": summary_code, "recommendation_codes": recommendations, "model_version": "deterministic_screening_rules_v2_not_diagnostic", "explanation": {"components": components, "weighted_contributions": contributions, "medical_disclaimer": "EyeInsight provides behavioral screening support only; it does not diagnose any condition."}}
