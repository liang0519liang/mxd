# 数据集目录

- `raw_frames/`：`extract_frames.py` 抽取的视频帧。
- `labels/`：网页标注页保存的 YOLO 标签；即使某张图没有目标，也必须点击“保存”产生空 `.txt`，让训练包含负样本。
- `yolo/`：`prepare_dataset.py` 自动生成的 train/val 划分与 `data.yaml`；可删除后重建。

类别编号固定：`0=player`、`1=monster`、`2=drop`。不要在不同地图/角色的数据集中复用同一模型，除非该模型已覆盖这些外观。
