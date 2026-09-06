from pathlib import Path

from services import demo_session_service


def test_demo_artifacts_are_synthetic_and_complete(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(demo_session_service, "FEATURES_DIR", str(tmp_path))

    output = demo_session_service.create_demo_artifacts("demo-test")

    assert output["session_features"]["demo_mode"] is True
    assert output["session_features"]["demo_data_type"] == "synthetic_no_personal_data"
    assert output["session_features"]["visualization_data"]["gaze_path"]
    assert set(output["feature_paths"]) == {"frame_features", "phase_features", "session_features", "session_features_json"}
    assert (tmp_path / "demo-test" / "analysis_result.json").is_file()
