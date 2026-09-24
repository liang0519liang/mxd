"""Central Phase 1 configuration for the MapleStory visual assistant.

All coordinates are physical pixels relative to the Win32 client area.  Real input
is intentionally not implemented in this phase; DRY_RUN remains a safety guard
for later phases.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class WindowConfig:
    """Game-window discovery and validation settings."""

    # 中文：游戏窗口标题关键字；English: substring used to find the game window.
    # 单位/Unit: text. Please replace after checking the actual window title.
    title_keyword: str = "MapleStory"
    # 中文：期望客户区宽度；English: expected client-area width.
    # 单位/Unit: physical pixels. A mismatch is a warning, not an automatic action.
    expected_client_width_px: int = 1366
    # 中文：期望客户区高度；English: expected client-area height.
    # 单位/Unit: physical pixels. Confirm after Windows DPI calibration.
    expected_client_height_px: int = 768
    # 中文：是否要求游戏窗口位于前台；English: require the game to be foreground.
    # 单位/Unit: boolean. Phase 1 only reports this condition.
    require_game_focus: bool = True
    # 中文：窗口状态复查间隔；English: period for revalidating the window.
    # 单位/Unit: seconds. Suggested range: 0.2 to 2.0 seconds.
    window_check_interval_s: float = 0.5
    # 中文：采集帧率上限；English: maximum capture frame rate.
    # 单位/Unit: FPS. Tune after measuring CPU use; 30 is a conservative start.
    capture_fps_limit: int = 30


@dataclass(frozen=True)
class RoiConfig:
    """Battle ROI relative to the game client area's top-left corner."""

    # 中文：ROI 左上角 X；English: ROI x offset from client top-left.
    # 单位/Unit: physical pixels. Must be calibrated in the preview overlay.
    x_px: int = 0
    # 中文：ROI 左上角 Y；English: ROI y offset from client top-left.
    # 单位/Unit: physical pixels. Must be calibrated in the preview overlay.
    y_px: int = 0
    # 中文：ROI 宽度；English: ROI width.
    # 单位/Unit: physical pixels. Must not exceed the client area.
    width_px: int = 1366
    # 中文：ROI 高度；English: ROI height.
    # 单位/Unit: physical pixels. Must not exceed the client area.
    height_px: int = 768


@dataclass(frozen=True)
class DebugConfig:
    """Read-only preview settings."""

    # 中文：调试模式；English: enable diagnostic output.
    # 单位/Unit: boolean.
    debug_mode: bool = True
    # 中文：演练模式；English: show decisions but never send input.
    # 单位/Unit: boolean. Must remain True until a later approved phase.
    dry_run: bool = True
    # 中文：显示 ROI 边界；English: show the ROI boundary in the client preview.
    # 单位/Unit: boolean.
    show_roi: bool = True


WINDOW = WindowConfig()
ROI = RoiConfig()
DEBUG = DebugConfig()
