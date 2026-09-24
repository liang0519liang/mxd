"""命令行入口：预览、纯视觉检测和安全的自动控制模式。"""
from __future__ import annotations

import argparse
import logging
import time

import cv2

import config
from capture import CaptureError, GameCapture
from controller import KeyboardController
from detector import TemplateDetector, draw_detections, draw_player_detection, load_monster_templates, player_from_result
from state_machine import BotStateMachine, Observation


def configure_logging() -> None:
    config.LOG_DIR.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(config.LOG_DIR / "bot.log", encoding="utf-8"), logging.StreamHandler()],
    )


def draw_status(frame, result, player_result, player_found: bool, state: str, attacking: bool) -> None:
    """把计数、阈值和未命中模板的最高置信度直接显示在 detect 窗口。"""
    lines = [
        f"state={state}  monsters={len(result.detections)}  attack={attacking}",
        f"monster reliable={result.reliable} threshold={config.MATCH_THRESHOLD:.3f} best={result.best_score if result.best_score is not None else -1:.3f}",
        f"player found={player_found} threshold={config.PLAYER_MATCH_THRESHOLD:.3f} best={player_result.best_score if player_result.best_score is not None else -1:.3f}",
    ]
    if result.error:
        lines.append(f"monster error: {result.error}")
    elif result.template_scores:
        scores = " | ".join(f"{name}:{score:.3f}" for name, score in sorted(result.template_scores.items()))
        lines.append(("monster max: " + scores)[:180])
    if player_result.error:
        lines.append(f"player error: {player_result.error}")
    elif player_result.template_scores:
        player_scores = " | ".join(f"{name}:{score:.3f}" for name, score in sorted(player_result.template_scores.items()))
        lines.append(("player max: " + player_scores)[:180])
    for index, line in enumerate(lines):
        cv2.putText(frame, line, (15, 30 + index * 27), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 255, 255), 2, cv2.LINE_AA)


def run(mode: str, enable_input: bool = False) -> None:
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

    input_active = mode == "auto" and (enable_input or not config.DEBUG_MODE)
    if mode == "auto" and not input_active:
        raise SystemExit(
            "自动模式默认禁止发送输入：请在 config.py 设置 DEBUG_MODE = False，"
            "或明确运行 python main.py auto --enable-input。"
        )
    controller = KeyboardController(enabled=input_active)
    state_machine = BotStateMachine(controller)
    try:
        while True:
            try:
                frame = capture.capture_game_frame(require_foreground=mode == "auto")
                roi = capture.capture_roi(frame)
                result = monster_detector.detect(roi)
                player_result = player_detector.detect(frame)
                player = player_from_result(player_result)
                if mode == "auto":
                    state_machine.step(Observation(result, player, emergency=controller.emergency_pressed()))

                visual = draw_detections(frame, result.detections)
                visual = draw_player_detection(visual, player)
                cv2.rectangle(visual, (config.ROI_LEFT, config.ROI_TOP), (config.ROI_LEFT + config.ROI_WIDTH, config.ROI_TOP + config.ROI_HEIGHT), (255, 0, 0), 2)
                draw_status(visual, result, player_result, player is not None, state_machine.state.value, config.ATTACK_KEY in controller.down)
                log.debug("detect: monsters=%d monster_scores=%s player=%s player_scores=%s", len(result.detections), result.template_scores, player is not None, player_result.template_scores)
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
    parser.add_argument("--enable-input", action="store_true", help="仅 auto：明确允许 pydirectinput 向前台游戏窗口发送按键")
    args = parser.parse_args()
    run(args.mode, enable_input=args.enable_input)
