"""Phase 1 entry point: read-only game-window ROI preview."""

from __future__ import annotations

import argparse
import importlib
import time

from capture import GameWindowCapture
from config import DEBUG, ROI, WINDOW


def run_preview() -> None:
    """Show the configured ROI; no keyboard or mouse input is ever sent."""
    cv2 = importlib.import_module("cv2")
    capture = GameWindowCapture(WINDOW, ROI)
    capture.open()
    try:
        frame_period_s = 1.0 / WINDOW.capture_fps_limit
        while True:
            started = time.monotonic()
            frame, status, screen_roi = capture.capture_roi()
            preview = frame[:, :, :3]
            label = (
                f"client=({status.client_rect.left},{status.client_rect.top}) "
                f"{status.client_rect.width}x{status.client_rect.height}; "
                f"roi=({screen_roi.left},{screen_roi.top}) {screen_roi.width}x{screen_roi.height}"
            )
            cv2.putText(preview, label, (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1, cv2.LINE_AA)
            cv2.imshow("MapleStory Phase 1 - ROI Preview (read-only)", preview)
            if cv2.waitKey(1) & 0xFF in (27, ord("q")):
                break
            remaining = frame_period_s - (time.monotonic() - started)
            if remaining > 0:
                time.sleep(remaining)
    finally:
        capture.close()
        cv2.destroyAllWindows()


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only Phase 1 game-window ROI preview")
    parser.add_argument("--preview", action="store_true", help="open the ROI preview window")
    args = parser.parse_args()
    if not args.preview:
        parser.error("Phase 1 only supports --preview; it never sends game input")
    if not DEBUG.dry_run:
        raise RuntimeError("Phase 1 requires DEBUG.dry_run=True")
    run_preview()


if __name__ == "__main__":
    main()
