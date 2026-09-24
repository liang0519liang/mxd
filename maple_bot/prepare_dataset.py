"""验证标注完整性，固定随机种子划分 train/val，并生成 YOLO data.yaml。"""
from __future__ import annotations
import argparse, random, shutil
from pathlib import Path
CLASSES=["player","monster","drop"]

def main() -> None:
 p=argparse.ArgumentParser();p.add_argument("--images",type=Path,default=Path("dataset/raw_frames"));p.add_argument("--labels",type=Path,default=Path("dataset/labels"));p.add_argument("--output",type=Path,default=Path("dataset/yolo"));p.add_argument("--val-ratio",type=float,default=.2);args=p.parse_args()
 if not 0<args.val_ratio<1: raise SystemExit("--val-ratio 必须在 0 与 1 之间")
 images=[x for x in sorted(args.images.iterdir()) if x.suffix.lower() in {'.jpg','.jpeg','.png'}]
 if not images: raise SystemExit("没有抽取帧")
 missing=[x.name for x in images if not (args.labels/f'{x.stem}.txt').exists()]
 if missing: raise SystemExit(f"仍有 {len(missing)} 张未保存标注（包括无目标空标签）：例如 {missing[:5]}")
 random.Random(20260924).shuffle(images);cut=max(1,round(len(images)*(1-args.val_ratio))); splits={"train":images[:cut],"val":images[cut:]}
 if not splits['val']: raise SystemExit("至少需要 2 张图")
 if args.output.exists(): shutil.rmtree(args.output)
 for split,items in splits.items():
  for image in items:
   target_i=args.output/'images'/split;target_l=args.output/'labels'/split;target_i.mkdir(parents=True,exist_ok=True);target_l.mkdir(parents=True,exist_ok=True)
   shutil.copy2(image,target_i/image.name);shutil.copy2(args.labels/f'{image.stem}.txt',target_l/f'{image.stem}.txt')
 yaml=args.output/'data.yaml';yaml.write_text(f"path: {args.output.resolve()}\ntrain: images/train\nval: images/val\nnames: {CLASSES}\n",encoding='utf-8')
 print(f"已生成 {yaml}：train={len(splits['train'])} val={len(splits['val'])}")
if __name__=='__main__':main()
