"""OpenCV 模板检测与可视化辅助函数。"""
from __future__ import annotations

from dataclasses import dataclass, field
import logging
from pathlib import Path

import cv2
import numpy as np

import config

LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class Detection:
    """以游戏客户区为基准的检测框中心。"""

    x: int
    y: int
    confidence: float
    template_name: str
    width: int = 0
    height: int = 0


@dataclass(frozen=True)
class DetectionResult:
    detections: list[Detection]
    reliable: bool
    error: str | None = None
    # 即使没有越过阈值也保留每个模板的最高分，供 detect 模式调参。
    template_scores: dict[str, float] = field(default_factory=dict)

    @property
    def best_score(self) -> float | None:
        return max(self.template_scores.values(), default=None)


class TemplateDetector:
    def __init__(self, template_dir: Path, threshold: float, min_distance: int, roi_offset: tuple[int, int] = (0, 0)):
        self.template_dir = Path(template_dir)
        self.threshold = threshold
        self.min_distance = min_distance
        self.roi_offset = roi_offset
        self.templates: list[tuple[str, np.ndarray]] = []

    def load(self) -> list[tuple[str, np.ndarray]]:
        self.templates = []
        if not self.template_dir.exists():
            LOG.warning("模板目录不存在：%s", self.template_dir)
            return self.templates
        for path in sorted(self.template_dir.iterdir()):
            if path.suffix.lower() not in config.SUPPORTED_IMAGE_SUFFIXES:
                continue
            image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
            if image is None or image.size == 0:
                LOG.warning("模板加载失败：%s（OpenCV 无法读取图片）", path)
                continue
            if float(image.std()) < 1.0:
                LOG.warning("模板加载失败：%s（图像几乎为纯色，不能用于模板匹配）", path)
                continue
            self.templates.append((path.name, image))
        LOG.info("从 %s 加载 %d 个模板", self.template_dir, len(self.templates))
        return self.templates

    def detect(self, frame: np.ndarray) -> DetectionResult:
        if not self.templates:
            return DetectionResult([], False, "没有可用模板")
        if frame is None or frame.size == 0:
            return DetectionResult([], False, "帧为空")
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            raw: list[Detection] = []
            scores: dict[str, float] = {}
            for name, template in self.templates:
                height, width = template.shape[:2]
                if height > gray.shape[0] or width > gray.shape[1]:
                    LOG.warning("跳过模板 %s：模板 %dx%d 大于 ROI %dx%d", name, width, height, gray.shape[1], gray.shape[0])
                    scores[name] = -1.0
                    continue
                response = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
                _, max_score, _, _ = cv2.minMaxLoc(response)
                scores[name] = float(max_score)
                y_positions, x_positions = np.where(response >= self.threshold)
                for y, x in zip(y_positions, x_positions):
                    raw.append(Detection(x + width // 2 + self.roi_offset[0], y + height // 2 + self.roi_offset[1], float(response[y, x]), name, width, height))
            return DetectionResult(deduplicate(raw, self.min_distance), True, template_scores=scores)
        except cv2.error as exc:
            return DetectionResult([], False, f"OpenCV 检测失败：{exc}")


def deduplicate(detections: list[Detection], min_distance: int) -> list[Detection]:
    kept: list[Detection] = []
    for detection in sorted(detections, key=lambda item: item.confidence, reverse=True):
        if all((detection.x - existing.x) ** 2 + (detection.y - existing.y) ** 2 >= min_distance ** 2 for existing in kept):
            kept.append(detection)
    return kept


def load_monster_templates() -> TemplateDetector:
    detector = TemplateDetector(config.TEMPLATE_DIR, config.MATCH_THRESHOLD, config.MONSTER_MIN_DISTANCE, (config.ROI_LEFT, config.ROI_TOP))
    detector.load()
    return detector


def detect_monsters(frame: np.ndarray, detector: TemplateDetector | None = None) -> DetectionResult:
    return (detector or load_monster_templates()).detect(frame)


def detect_player(frame: np.ndarray, detector: TemplateDetector | None = None) -> Detection | None:
    detector = detector or TemplateDetector(config.PLAYER_TEMPLATE_DIR, config.PLAYER_MATCH_THRESHOLD, config.MONSTER_MIN_DISTANCE)
    if not detector.templates:
        detector.load()
    result = detector.detect(frame)
    if not result.reliable or not result.detections:
        return None
    best = max(result.detections, key=lambda item: item.confidence)
    return Detection(best.x, best.y + best.height // 2, best.confidence, best.template_name, best.width, best.height)


def draw_detections(frame: np.ndarray, detections: list[Detection]) -> np.ndarray:
    output = frame.copy()
    for detection in detections:
        left = detection.x - detection.width // 2
        top = detection.y - detection.height // 2
        right = left + detection.width
        bottom = top + detection.height
        cv2.rectangle(output, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.circle(output, (detection.x, detection.y), 3, (0, 0, 255), -1)
        cv2.putText(output, f"{detection.template_name} {detection.confidence:.3f}", (left, max(16, top - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
    return output
