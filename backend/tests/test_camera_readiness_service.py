from services.camera_readiness_service import summarize_camera_observations


def _observation(**overrides):
    return {
        "brightness": 120.0,
        "face_detected": 1,
        "face_area_ratio": 0.12,
        "center_offset": 0.08,
        "head_stability": 0.92,
        **overrides,
    }


def test_camera_readiness_passes_when_all_checks_are_good() -> None:
    result = summarize_camera_observations([_observation() for _ in range(4)])

    assert result["ready"] is True
    assert all(result["checks"].values())
    assert result["issues"] == []


def test_camera_readiness_reports_actionable_issues() -> None:
    observations = [
        _observation(brightness=30.0, face_area_ratio=0.02, center_offset=0.4, head_stability=0.2)
        for _ in range(4)
    ]

    result = summarize_camera_observations(observations)

    assert result["ready"] is False
    assert set(result["issues"]) == {"lighting_low", "face_not_centered", "face_too_far", "camera_unstable"}
