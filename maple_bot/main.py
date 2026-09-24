"""YOLO 主入口：preview、detect、auto。每个 YOLO 权重对应一张地图配置。"""
from __future__ import annotations
import argparse
import logging
import time
import cv2
import config
from capture import CaptureError, GameCapture
from controller import KeyboardController
from state_machine import BotStateMachine, Observation
from detector import DetectionResult
from yolo_detector import SceneResult, YoloDetector, draw_scene

def configure_logging() -> None:
    config.LOG_DIR.mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", handlers=[logging.FileHandler(config.LOG_DIR / "bot.log", encoding="utf-8"), logging.StreamHandler()])

def in_roi(detection) -> bool:
    return config.ROI_LEFT <= detection.x < config.ROI_LEFT + config.ROI_WIDTH and config.ROI_TOP <= detection.y < config.ROI_TOP + config.ROI_HEIGHT

def draw_status(frame, scene, state, input_active) -> None:
    lines = [
        f"YOLO state={state} input={input_active}",
        f"monsters={len(scene.monsters.detections)} player={scene.player is not None} conf={config.YOLO_CONFIDENCE:.2f}",
        "green=monster orange=player cyan=drop | q/ESC exit",
    ]
    for index, line in enumerate(lines): cv2.putText(frame, line, (15, 30 + index * 26), cv2.FONT_HERSHEY_SIMPLEX, .58, (0, 255, 255), 2, cv2.LINE_AA)

def run(mode: str, enable_input: bool = False) -> None:
    configure_logging()
    detector = YoloDetector(); detector.load()
    input_active = mode == "auto" and (enable_input or not config.DEBUG_MODE)
    if mode == "auto" and not input_active:
        raise SystemExit("自动模式默认禁止输入：运行 python main.py auto --enable-input，或设置 DEBUG_MODE=False。")
    capture = GameCapture()
    controller = KeyboardController(enabled=input_active)
    machine = BotStateMachine(controller)
    try:
        while True:
            try:
                frame = capture.capture_game_frame(require_foreground=mode == "auto")
                scene = detector.detect(frame)
                monsters = [monster for monster in scene.monsters.detections if in_roi(monster)]
                scene = SceneResult(DetectionResult(monsters, scene.monsters.reliable, scene.monsters.error), scene.player, scene.drops)
                if mode == "auto": machine.step(Observation(scene.monsters, scene.player, emergency=controller.emergency_pressed()))
                visual = draw_scene(frame, scene)
                cv2.rectangle(visual, (config.ROI_LEFT, config.ROI_TOP), (config.ROI_LEFT + config.ROI_WIDTH, config.ROI_TOP + config.ROI_HEIGHT), (255, 0, 0), 2)
                draw_status(visual, scene, machine.state.value, input_active)
                if mode in ("preview", "detect"):
                    cv2.imshow("Maple YOLO Debug", visual)
                    if cv2.waitKey(1) & 0xFF in (ord("q"), 27): break
                if config.SAVE_DEBUG_IMAGES:
                    config.DEBUG_DIR.mkdir(exist_ok=True); cv2.imwrite(str(config.DEBUG_DIR / "latest.jpg"), visual)
                if not scene.monsters.detections:
                    time.sleep(config.NO_MONSTER_WAIT_SECONDS)
                else:
                    time.sleep(config.IDLE_INTERVAL if mode == "preview" else config.APPROACH_INTERVAL)
            except CaptureError as exc:
                controller.release_all_keys(); logging.warning("截图不可用：%s", exc); time.sleep(1)
    finally:
        controller.release_all_keys(); cv2.destroyAllWindows()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["preview", "detect", "auto"], nargs="?", default="preview")
    parser.add_argument("--enable-input", action="store_true")
    args = parser.parse_args(); run(args.mode, args.enable_input)
