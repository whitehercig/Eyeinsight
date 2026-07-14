from services.risk_model_service import score_from_session_features


def test_risk_score_is_deterministic_and_explainable() -> None:
    features = {
        "attention_score": 82.0,
        "overall_tracking_quality": 0.9,
        "overall_face_visibility": 0.95,
        "overall_looking_away_ratio": 0.08,
        "overall_center_fixation": 0.86,
        "overall_head_stability": 0.88,
        "overall_gaze_stability": 0.84,
        "overall_usable_frames": 0.9,
        "overall_quality_score": 92.0,
    }

    first = score_from_session_features(features)
    second = score_from_session_features(features)

    assert first == second
    assert first["risk_level"] == "low"
    assert 0 <= first["risk_score"] <= 100
    assert 0 <= first["confidence"] <= 100
    assert first["confidence_type"] == "technical_input_reliability_not_clinical_probability"
    assert first["top_contributing_factors"]


def test_lower_attention_increases_indicator_score() -> None:
    baseline = {"attention_score": 90, "overall_tracking_quality": .9, "overall_face_visibility": .9, "overall_looking_away_ratio": .05, "overall_center_fixation": .9, "overall_head_stability": .9, "overall_gaze_stability": .9, "overall_usable_frames": .9, "overall_quality_score": 90}
    lower_attention = {**baseline, "attention_score": 25, "overall_tracking_quality": .35, "overall_looking_away_ratio": .7}

    assert score_from_session_features(lower_attention)["risk_score"] > score_from_session_features(baseline)["risk_score"]
