"""独立的 Win32 客户区定位与 mss 截图模块。"""
from __future__ import annotations
from dataclasses import dataclass
import ctypes
import sys
from typing import Iterable
import numpy as np
import cv2
import mss
import config

class CaptureError(RuntimeError): pass
class WindowUnavailable(CaptureError): pass
class RoiConfigurationError(CaptureError): pass

@dataclass(frozen=True)
class ClientRect:
    left: int; top: int; width: int; height: int

class GameCapture:
    def __init__(self, title_keyword: str = config.WINDOW_TITLE_KEYWORD):
        self.title_keyword = title_keyword
        if sys.platform == "win32":
            ctypes.windll.user32.SetProcessDPIAware()

    def _windows(self) -> Iterable[tuple[int, str]]:
        if sys.platform != "win32": raise WindowUnavailable("窗口截图仅支持 Windows/Win32 API")
        import win32gui
        result = []
        def callback(hwnd, _):
            title = win32gui.GetWindowText(hwnd)
            if win32gui.IsWindowVisible(hwnd) and self.title_keyword.lower() in title.lower(): result.append((hwnd, title))
        win32gui.EnumWindows(callback, None)
        return result

    def client_rect(self) -> ClientRect:
        matches = list(self._windows())
        if not matches: raise WindowUnavailable(f"未找到标题含“{self.title_keyword}”的窗口")
        if len(matches) > 1: raise WindowUnavailable("匹配到多个窗口，请设置更精确的 WINDOW_TITLE_KEYWORD：" + ", ".join(t for _, t in matches))
        import win32gui
        hwnd, _ = matches[0]
        if win32gui.IsIconic(hwnd): raise WindowUnavailable("游戏窗口已最小化")
        if win32gui.GetForegroundWindow() != hwnd: raise WindowUnavailable("游戏窗口未获得焦点")
        left, top = win32gui.ClientToScreen(hwnd, (0, 0))
        _, _, width, height = win32gui.GetClientRect(hwnd)
        if (width, height) != (config.EXPECTED_CLIENT_WIDTH, config.EXPECTED_CLIENT_HEIGHT):
            raise WindowUnavailable(f"客户区尺寸异常：{width}x{height}，期望 {config.EXPECTED_CLIENT_WIDTH}x{config.EXPECTED_CLIENT_HEIGHT}")
        return ClientRect(left, top, width, height)

    def capture_game_frame(self) -> np.ndarray:
        r = self.client_rect()
        with mss.mss() as sct:
            shot = np.asarray(sct.grab({"left": r.left, "top": r.top, "width": r.width, "height": r.height}))
        return cv2.cvtColor(shot, cv2.COLOR_BGRA2BGR)

    @staticmethod
    def capture_roi(frame: np.ndarray) -> np.ndarray:
        h, w = frame.shape[:2]; x, y, rw, rh = config.ROI_LEFT, config.ROI_TOP, config.ROI_WIDTH, config.ROI_HEIGHT
        if x < 0 or y < 0 or rw <= 0 or rh <= 0 or x + rw > w or y + rh > h:
            raise RoiConfigurationError(f"ROI ({x},{y},{rw},{rh}) 超出帧范围 {w}x{h}")
        return frame[y:y+rh, x:x+rw].copy()

def capture_game_frame() -> np.ndarray: return GameCapture().capture_game_frame()
def capture_roi(frame: np.ndarray) -> np.ndarray: return GameCapture.capture_roi(frame)
