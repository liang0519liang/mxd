"""从录制视频均匀抽帧，供人工标注；不会创建或猜测标签。"""
from __future__ import annotations
import argparse
from pathlib import Path
import cv2

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("video", type=Path)
    parser.add_argument("--output", type=Path, default=Path("dataset/raw_frames"))
    parser.add_argument("--every-seconds", type=float, default=0.5, help="抽帧间隔；建议 0.3~1.0")
    parser.add_argument("--max-frames", type=int, default=0, help="0 表示不限制")
    args = parser.parse_args()
    if not args.video.is_file(): raise SystemExit(f"找不到视频：{args.video}")
    if args.every_seconds <= 0: raise SystemExit("--every-seconds 必须大于 0")
    args.output.mkdir(parents=True, exist_ok=True)
    capture = cv2.VideoCapture(str(args.video))
    fps = capture.get(cv2.CAP_PROP_FPS)
    if fps <= 0: raise SystemExit("无法读取视频 FPS")
    step = max(1, round(fps * args.every_seconds)); index = saved = 0
    while True:
        ok, frame = capture.read()
        if not ok: break
        if index % step == 0:
            path = args.output / f"frame_{saved:06d}.jpg"
            if not cv2.imwrite(str(path), frame): raise SystemExit(f"无法写入：{path}")
            saved += 1
            if args.max_frames and saved >= args.max_frames: break
        index += 1
    capture.release()
    print(f"已抽取 {saved} 帧到 {args.output.resolve()}")
if __name__ == "__main__": main()
