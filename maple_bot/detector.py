"""可扩展的 OpenCV 模板检测；检测失败与“可靠地检测到 0 只”严格区分。"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import logging
import cv2
import numpy as np
import config

LOG = logging.getLogger(__name__)
@dataclass(frozen=True)
class Detection:
    x: int; y: int; confidence: float; template_name: str
    width: int = 0; height: int = 0
@dataclass(frozen=True)
class DetectionResult:
    detections: list[Detection]; reliable: bool; error: str | None = None

class TemplateDetector:
    def __init__(self, template_dir: Path, threshold: float, min_distance: int, roi_offset: tuple[int,int] = (0,0)):
        self.template_dir, self.threshold, self.min_distance, self.roi_offset = Path(template_dir), threshold, min_distance, roi_offset
        self.templates: list[tuple[str, np.ndarray]] = []
    def load(self) -> list[tuple[str,np.ndarray]]:
        self.templates = []
        if not self.template_dir.exists():
            LOG.warning("模板目录不存在：%s", self.template_dir); return self.templates
        for path in sorted(self.template_dir.iterdir()):
            if path.suffix.lower() not in config.SUPPORTED_IMAGE_SUFFIXES: continue
            image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
            if image is None or image.size == 0: LOG.warning("模板加载失败：%s", path); continue
            self.templates.append((path.name, image))
        LOG.info("从 %s 加载 %d 个模板", self.template_dir, len(self.templates)); return self.templates
    def detect(self, frame: np.ndarray) -> DetectionResult:
        if not self.templates: return DetectionResult([], False, "没有可用模板")
        if frame is None or frame.size == 0: return DetectionResult([], False, "帧为空")
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            raw=[]
            for name, templ in self.templates:
                th, tw = templ.shape[:2]
                if th > gray.shape[0] or tw > gray.shape[1]: continue
                result=cv2.matchTemplate(gray, templ, cv2.TM_CCOEFF_NORMED)
                ys,xs=np.where(result >= self.threshold)
                for y,x in zip(ys,xs): raw.append(Detection(x+tw//2+self.roi_offset[0], y+th//2+self.roi_offset[1], float(result[y,x]), name, tw, th))
            return DetectionResult(deduplicate(raw, self.min_distance), True)
        except cv2.error as exc: return DetectionResult([], False, f"OpenCV 检测失败：{exc}")

def deduplicate(detections: list[Detection], min_distance: int) -> list[Detection]:
    kept=[]
    for d in sorted(detections, key=lambda item:item.confidence, reverse=True):
        if all((d.x-k.x)**2 + (d.y-k.y)**2 >= min_distance**2 for k in kept): kept.append(d)
    return kept

def load_monster_templates() -> TemplateDetector:
    d=TemplateDetector(config.TEMPLATE_DIR, config.MATCH_THRESHOLD, config.MONSTER_MIN_DISTANCE, (config.ROI_LEFT,config.ROI_TOP)); d.load(); return d
def detect_monsters(frame: np.ndarray, detector: TemplateDetector | None = None) -> DetectionResult:
    return (detector or load_monster_templates()).detect(frame)
def detect_player(frame: np.ndarray, detector: TemplateDetector | None = None) -> Detection | None:
    d=detector or TemplateDetector(config.PLAYER_TEMPLATE_DIR, config.PLAYER_MATCH_THRESHOLD, config.MONSTER_MIN_DISTANCE); 
    if not d.templates: d.load()
    result=d.detect(frame)
    if not result.reliable or not result.detections: return None
    best=max(result.detections,key=lambda i:i.confidence)
    return Detection(best.x, best.y + best.height//2, best.confidence, best.template_name, best.width,best.height)
def draw_detections(frame: np.ndarray, detections: list[Detection]) -> np.ndarray:
    out=frame.copy()
    for d in detections:
        cv2.rectangle(out,(d.x-d.width//2,d.y-d.height//2),(d.x+d.width//2,d.y+d.height//2),(0,255,0),1); cv2.circle(out,(d.x,d.y),3,(0,0,255),-1)
        cv2.putText(out,f"{d.template_name}:{d.confidence:.2f}",(d.x,d.y-8),cv2.FONT_HERSHEY_SIMPLEX,.4,(0,255,0),1)
    return out
