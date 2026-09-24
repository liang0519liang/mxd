import pytest

from capture import Rect, roi_to_screen_rect, validate_relative_roi
from config import RoiConfig


def test_roi_to_screen_rect_keeps_client_relative_coordinates() -> None:
    client = Rect(left=1400, top=100, width=1366, height=768)
    roi = RoiConfig(x_px=30, y_px=120, width_px=900, height_px=500)

    assert roi_to_screen_rect(client, roi) == Rect(left=1430, top=220, width=900, height=500)


@pytest.mark.parametrize(
    "roi",
    [
        RoiConfig(width_px=0),
        RoiConfig(x_px=-1),
        RoiConfig(x_px=1300, width_px=100),
        RoiConfig(y_px=700, height_px=100),
    ],
)
def test_invalid_roi_is_rejected(roi: RoiConfig) -> None:
    with pytest.raises(ValueError):
        validate_relative_roi(roi, client_width=1366, client_height=768)
