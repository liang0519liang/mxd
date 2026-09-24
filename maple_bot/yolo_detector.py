"""本地 Ultralytics YOLO 推理适配器；不附带模型或训练数据。"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import logging
import numpy as np
import config
from detector import Detection, DetectionResult, draw_detections

LOG = logging.getLogger(__name__)

@dataclass(frozen=True)
class SceneResult:
    monsters: DetectionResult
    player: Detection | None
    drops: list[Detection]

class YoloDetector:
    def __init__(self, model_path: Path = config.YOLO_MODEL_PATH):
        self.model_path = Path(model_path)
        self.model = None

    def load(self) -> None:
        if not self.model_path.is_file():
            raise FileNotFoundError(f"未找到 YOLO 模型：{self.model_path}。请先训练并复制 best.pt 到此路径，或修改 YOLO_MODEL_PATH。")
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError("缺少 ultralytics；请执行 pip install -r requirements.txt") from exc
        self.model = YOLO(str(self.model_path))
        LOG.info("已加载 YOLO 模型：%s", self.model_path)

    def detect(self, frame: np.ndarray) -> SceneResult:
        if self.model is None:
            return SceneResult(DetectionResult([], False, "YOLO 模型尚未加载"), None, [])
        try:
            result = self.model.predict(frame, conf=config.YOLO_CONFIDENCE, iou=config.YOLO_IOU_THRESHOLD, device=config.YOLO_DEVICE, verbose=False)[0]
            names = result.names
            monsters: list[Detection] = []
            players: list[Detection] = []
            drops: list[Detection] = []
            for box in result.boxes:
                x1, y1, x2, y2 = (int(v) for v in box.xyxy[0].tolist())
                confidence = float(box.conf[0])
                name = str(names[int(box.cls[0])]).lower()
                detection = Detection((x1 + x2) // 2, (y1 + y2) // 2, confidence, name, x2 - x1, y2 - y1)
                if name == config.MONSTER_CLASS_NAME.lower(): monsters.append(detection)
                elif name == config.PLAYER_CLASS_NAME.lower(): players.append(detection)
                elif name == config.DROP_CLASS_NAME.lower(): drops.append(detection)
            player = max(players, key=lambda item: item.confidence, default=None)
            return SceneResult(DetectionResult(monsters, True), player, drops)
        except Exception as exc:
            LOG.exception("YOLO 推理失败")
            return SceneResult(DetectionResult([], False, f"YOLO 推理失败：{exc}"), None, [])

def draw_scene(frame: np.ndarray, scene: SceneResult) -> np.ndarray:
    output = draw_detections(frame, scene.monsters)
    import cv2
    if scene.player is not None:
        player = scene.player
        x1, y1 = player.x-player.width//2, player.y-player.height//2
        cv2.rectangle(output, (x1, y1), (x1+player.width, y1+player.height), (0, 165, 255), 2)
        cv2.circle(output, (player.x, y1+player.height), 4, (0, 0, 255), -1)
        cv2.putText(output, f"player {player.confidence:.2f}", (x1, max(15, y1-4)), cv2.FONT_HERSHEY_SIMPLEX, .45, (0,165,255), 1)
    # 掉落物用青色框，仅可视化，不参与移动决策。
    for item in scene.drops:
        x1, y1 = item.x-item.width//2, item.y-item.height//2
        cv2.rectangle(output, (x1, y1), (x1+item.width, y1+item.height), (255, 255, 0), 1)
        cv2.putText(output, f"drop {item.confidence:.2f}", (x1, max(15, y1-4)), cv2.FONT_HERSHEY_SIMPLEX, .45, (255,255,0), 1)
    return output
