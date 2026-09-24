from config import DEBUG, ROI, WINDOW


def test_phase_one_defaults_are_safe_and_valid() -> None:
    assert DEBUG.dry_run is True
    assert WINDOW.capture_fps_limit > 0
    assert WINDOW.window_check_interval_s > 0
    assert ROI.width_px > 0
    assert ROI.height_px > 0
