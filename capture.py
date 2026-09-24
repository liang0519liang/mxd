"""Windows client-area capture for Phase 1; this module never sends input."""

from __future__ import annotations

import ctypes
import importlib
import sys
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import numpy as np

from config import RoiConfig, WindowConfig


@dataclass(frozen=True)
class Rect:
    """A physical-pixel rectangle with a top-left origin."""

    left: int
    top: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height


@dataclass(frozen=True)
class WindowStatus:
    """Latest state of the located game window."""

    handle: int
    title: str
    client_rect: Rect
    is_minimized: bool
    is_foreground: bool
    size_matches_expected: bool

    @property
    def safe_for_capture(self) -> bool:
        return not self.is_minimized and self.client_rect.width > 0 and self.client_rect.height > 0


def enable_per_monitor_dpi_awareness() -> None:
    """Request physical-pixel coordinates before querying window geometry."""
    if sys.platform != "win32":
        return
    # Windows 10+ API. Failure leaves Windows' current process DPI mode unchanged.
    ctypes.windll.user32.SetProcessDPIAware()


def validate_relative_roi(roi: RoiConfig, client_width: int, client_height: int) -> None:
    """Raise ValueError if a client-relative ROI is empty or out of bounds."""
    if roi.width_px <= 0 or roi.height_px <= 0:
        raise ValueError("ROI width and height must be positive")
    if roi.x_px < 0 or roi.y_px < 0:
        raise ValueError("ROI x and y must be non-negative")
    if roi.x_px + roi.width_px > client_width or roi.y_px + roi.height_px > client_height:
        raise ValueError("ROI must remain inside the game client area")


def roi_to_screen_rect(client_rect: Rect, roi: RoiConfig) -> Rect:
    """Convert a client-relative ROI to a physical screen rectangle."""
    validate_relative_roi(roi, client_rect.width, client_rect.height)
    return Rect(client_rect.left + roi.x_px, client_rect.top + roi.y_px, roi.width_px, roi.height_px)


class GameWindowCapture:
    """Find a Win32 window by title and capture only its validated ROI."""

    def __init__(self, window_config: WindowConfig, roi_config: RoiConfig) -> None:
        self._window_config = window_config
        self._roi_config = roi_config
        self._sct: Any | None = None
        self._last_window_check_monotonic = 0.0
        self._cached_status: WindowStatus | None = None

    @staticmethod
    def _require_windows() -> None:
        if sys.platform != "win32":
            raise RuntimeError("Game window capture is supported only on Windows")

    @staticmethod
    def _win32_modules() -> tuple[Any, Any]:
        """Load pywin32 at runtime so geometry helpers remain unit-testable elsewhere."""
        return importlib.import_module("win32gui"), importlib.import_module("win32con")

    def locate_window(self) -> WindowStatus:
        """Find the first visible top-level window containing the configured title."""
        self._require_windows()
        win32gui, win32con = self._win32_modules()
        keyword = self._window_config.title_keyword.casefold()
        candidates: list[tuple[int, str]] = []

        def collect(handle: int, _: object) -> None:
            if not win32gui.IsWindowVisible(handle):
                return
            title = win32gui.GetWindowText(handle)
            if keyword in title.casefold():
                candidates.append((handle, title))

        win32gui.EnumWindows(collect, None)
        if not candidates:
            raise RuntimeError(f"No visible window contains title keyword: {self._window_config.title_keyword!r}")

        handle, title = candidates[0]
        left_top = win32gui.ClientToScreen(handle, (0, 0))
        right_bottom = win32gui.ClientToScreen(handle, win32gui.GetClientRect(handle)[2:])
        client_rect = Rect(left_top[0], left_top[1], right_bottom[0] - left_top[0], right_bottom[1] - left_top[1])
        is_minimized = bool(win32gui.IsIconic(handle))
        foreground = win32gui.GetForegroundWindow() == handle
        expected = (
            client_rect.width == self._window_config.expected_client_width_px
            and client_rect.height == self._window_config.expected_client_height_px
        )
        _ = win32con  # Makes the required Win32 constant module explicit for later extensions.
        return WindowStatus(handle, title, client_rect, is_minimized, foreground, expected)

    def refresh_status(self, force: bool = False) -> WindowStatus:
        """Refresh geometry periodically so moved windows get new capture coordinates."""
        now = time.monotonic()
        if force or self._cached_status is None or now - self._last_window_check_monotonic >= self._window_config.window_check_interval_s:
            self._cached_status = self.locate_window()
            self._last_window_check_monotonic = now
        return self._cached_status

    def open(self) -> None:
        """Open the MSS capture session after Windows/DPI validation."""
        self._require_windows()
        enable_per_monitor_dpi_awareness()
        self._sct = importlib.import_module("mss").mss()

    def close(self) -> None:
        """Close MSS resources; safe to call during normal program shutdown."""
        if self._sct is not None:
            self._sct.close()
            self._sct = None

    def capture_roi(self) -> tuple[Any, WindowStatus, Rect]:
        """Return a BGRA ROI frame, current window status, and screen ROI rectangle."""
        if self._sct is None:
            raise RuntimeError("Capture is not open; call open() first")
        status = self.refresh_status()
        if not status.safe_for_capture:
            raise RuntimeError("Game window is minimized or has an invalid client area")
        if self._window_config.require_game_focus and not status.is_foreground:
            raise RuntimeError("Game window is not foreground while REQUIRE_GAME_FOCUS is enabled")
        screen_roi = roi_to_screen_rect(status.client_rect, self._roi_config)
        monitor = {"left": screen_roi.left, "top": screen_roi.top, "width": screen_roi.width, "height": screen_roi.height}
        numpy = importlib.import_module("numpy")
        return numpy.asarray(self._sct.grab(monitor)), status, screen_roi
