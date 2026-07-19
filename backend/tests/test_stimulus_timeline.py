from services.stimulus_timeline import get_target_at


def test_moving_target_changes_position_within_tracking_phase() -> None:
    early = get_target_at(5.0)
    later = get_target_at(5.9)

    assert early == {"x": 0.13, "y": 0.5, "zone": "moving_target"}
    assert later is not None
    assert later["x"] > early["x"]


def test_attention_shift_target_alternates_sides() -> None:
    assert get_target_at(35.5) == {"x": 0.18, "y": 0.5, "zone": "attention_shift_target"}
    assert get_target_at(36.5) == {"x": 0.82, "y": 0.5, "zone": "attention_shift_target"}


def test_target_is_missing_after_the_stimulus() -> None:
    assert get_target_at(50.1) is None
