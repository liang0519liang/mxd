"""YOLO 训练入口。视频须先人工抽帧并标注，训练不自动伪造标签。"""
from __future__ import annotations
import argparse
from pathlib import Path

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True, help="data.yaml（类别必须包含 player、monster、drop）")
    parser.add_argument("--model", default="yolo11n.pt", help="预训练起点或已有 .pt")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=960)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise SystemExit("缺少 ultralytics；请执行 pip install -r requirements.txt") from exc
    if not args.data.is_file(): raise SystemExit(f"找不到数据配置：{args.data}")
    model = YOLO(args.model)
    model.train(data=str(args.data), epochs=args.epochs, imgsz=args.imgsz, device=args.device, project="runs", name="maple")
if __name__ == "__main__": main()
