"""命令行入口：预览、纯视觉检测和安全的自动控制模式。"""
from __future__ import annotations

import argparse
import logging
import time

import cv2

import config
from capture import CaptureError, GameCapture
from controller import KeyboardController
from detector import TemplateDetector, detect_player, draw_detections, load_monster_templates
from state_machine import BotStateMachine, Observation


def configure_logging() -> None:
    config.LOG_DIR.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(config.LOG_DIR / "bot.log", encoding="utf-8"), logging.StreamHandler()],
    )


def draw_status(frame, result, state: str, attacking: bool) -> None:
    """把计数、阈值和未命中模板的最高置信度直接显示在 detect 窗口。"""
    lines = [
        f"state={state}  monsters={len(result.detections)}  attack={attacking}",
        f"reliable={result.reliable}  threshold={config.MATCH_THRESHOLD:.3f}  best={result.best_score if result.best_score is not None else -1:.3f}",
    ]
    if result.error:
        lines.append(f"error: {result.error}")
    elif result.template_scores:
        scores = " | ".join(f"{name}:{score:.3f}" for name, score in sorted(result.template_scores.items()))
        # cv2 文本过长会溢出，日志仍会保留完整模板分数。
        lines.append(("template max: " + scores)[:180])
    for index, line in enumerate(lines):
        cv2.putText(frame, line, (15, 30 + index * 27), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 255, 255), 2, cv2.LINE_AA)


def run(mode: str) -> None:
    configure_logging()
    log = logging.getLogger(__name__)
    capture = GameCapture()
    monster_detector = load_monster_templates()
    player_detector = TemplateDetector(config.PLAYER_TEMPLATE_DIR, config.PLAYER_MATCH_THRESHOLD, config.MONSTER_MIN_DISTANCE)
    player_detector.load()
    if not monster_detector.templates:
        raise SystemExit("未找到可用怪物模板：请在 templates/monsters/ 添加非纯色 PNG/JPG/BMP 后重试。")
    if mode == "auto" and not player_detector.templates:
        raise SystemExit("自动控制需要人物模板：请在 templates/player/ 添加模板。")

    controller = KeyboardController(enabled=mode == "auto" and not config.DEBUG_MODE)
    state_machine = BotStateMachine(controller)
    try:
        while True:
            try:
                frame = capture.capture_game_frame()
                roi = capture.capture_roi(frame)
                result = monster_detector.detect(roi)
                player = detect_player(frame, player_detector)
                if mode == "auto":
                    state_machine.step(Observation(result, player, emergency=controller.emergency_pressed()))

                visual = draw_detections(frame, result.detections)
                cv2.rectangle(visual, (config.ROI_LEFT, config.ROI_TOP), (config.ROI_LEFT + config.ROI_WIDTH, config.ROI_TOP + config.ROI_HEIGHT), (255, 0, 0), 2)
                draw_status(visual, result, state_machine.state.value, config.ATTACK_KEY in controller.down)
                log.debug("detect: count=%d, best=%s, per_template=%s", len(result.detections), result.best_score, result.template_scores)
                if mode in ("preview", "detect"):
                    cv2.imshow("Maple Bot Debug (q/ESC 退出)", visual)
                    if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                        break
                if config.SAVE_DEBUG_IMAGES:
                    config.DEBUG_DIR.mkdir(exist_ok=True)
                    cv2.imwrite(str(config.DEBUG_DIR / "latest.jpg"), visual)
                time.sleep(config.IDLE_INTERVAL if mode != "auto" else config.APPROACH_INTERVAL)
            except CaptureError as exc:
                controller.release_all_keys()
                log.warning("截图不可用：%s", exc)
                time.sleep(1)
    finally:
        controller.release_all_keys()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["preview", "detect", "auto"], nargs="?", default="preview")
    run(parser.parse_args().mode)
