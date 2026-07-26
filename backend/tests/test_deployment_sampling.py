from services.video_feature_service import _analysis_sampling_interval


def test_sampling_is_disabled_without_deployment_setting(monkeypatch) -> None:
    monkeypatch.delenv("EYEINSIGHT_MAX_ANALYSIS_FPS", raising=False)

    assert _analysis_sampling_interval(30.0) == 1


def test_sampling_limits_cloud_analysis_rate(monkeypatch) -> None:
    monkeypatch.setenv("EYEINSIGHT_MAX_ANALYSIS_FPS", "4")

    assert _analysis_sampling_interval(30.0) == 8
    assert _analysis_sampling_interval(24.0) == 6
