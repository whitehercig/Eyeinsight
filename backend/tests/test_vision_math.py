from services.vision_service import _normalize_pitch


def test_normalize_pitch_handles_equivalent_180_degree_pose() -> None:
    assert _normalize_pitch(173.0) == 7.0
    assert _normalize_pitch(-173.0) == -7.0
    assert _normalize_pitch(12.5) == 12.5
