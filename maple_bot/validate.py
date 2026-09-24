"""验证权重指标并将视频推理结果输出为带框视频。"""
from __future__ import annotations
import argparse
from pathlib import Path

def main() -> None:
 p=argparse.ArgumentParser();p.add_argument('--model',type=Path,required=True);p.add_argument('--data',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--conf',type=float,default=.45);p.add_argument('--device',default='cpu');args=p.parse_args()
 if not args.model.is_file() or not args.data.is_file() or not args.source.exists(): raise SystemExit('model、data 和 source 必须存在')
 try: from ultralytics import YOLO
 except ImportError as exc: raise SystemExit('缺少 ultralytics；请执行 pip install -r requirements.txt') from exc
 model=YOLO(str(args.model));metrics=model.val(data=str(args.data),device=args.device);print(f"mAP50-95={metrics.box.map:.4f}, mAP50={metrics.box.map50:.4f}")
 model.predict(source=str(args.source),conf=args.conf,device=args.device,save=True,project='runs',name='validate_video')
if __name__=='__main__':main()
