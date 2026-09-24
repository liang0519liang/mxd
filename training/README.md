# 数据集、训练与评估路线（Phase 0）

## 目录与标注

```text
datasets/maple_v1/
  images/{train,val,test}/
  labels/{train,val,test}/
training/dataset.yaml
models/{README.md,best.pt (后续产物)}
```

YOLO 每张图片对应同名 `.txt`；每行：`class_id x_center y_center width height`，四个坐标为 0–1 归一化值。类别固定为 `0: player, 1: monster, 2: loot`。`dataset.yaml` 后续声明三个图像目录及该映射。

## 从录像到部署

1. 在规则允许范围内录制不同地图/角色/分辨率条件的视频，并记录场景元数据。
2. `extract_frames.py`（Phase 2）按可配置间隔抽帧，并加场景变化或感知哈希去重，避免堆积近乎相同连续帧。
3. 使用 CVAT、Label Studio 或 Roboflow 本地/合规工作流标注三类框；复审随机样本，特别是小 loot 与遮挡。
4. **按录像片段/游戏会话分组**划分 train/val/test，禁止从同一连续片段把相邻帧随机拆到不同集合。
5. `train.py` 以 CUDA 启动轻量 YOLO；RTX 3060 12GB 先从 640、batch 8–16 试验，OOM 时先减 batch（16→8→4），再减 imgsz（640→512）。
6. `evaluate.py` 在从未参与调参的 test 会话上报告每类 Precision、Recall、mAP、混淆矩阵、漏检案例与推理时延；通过后将 `best.pt` 放进 `models/`，并把地图/角色/数据版本写入模型元数据。
7. `detector.py` 只加载已验证的模型；“加载模型”只表示它针对相应角色、怪物外观与地图组合进行了训练验证，绝不自动保证泛化到别的组合。

## 术语

|术语|项目中的含义|
|---|---|
|Dataset（数据集）|带图像与标注、并按 train/val/test 分割的 MapleStory 画面集合。|
|Annotation（标注）|人工为玩家、怪物、掉落物画框并赋类别的真值。|
|Bounding Box（边界框）|包围一个对象的矩形；玩家框的底部中心作为近似脚点。|
|Epoch|模型完整看过一次训练集；不是质量保证，应以验证曲线和测试集决定。|
|Batch Size|每次梯度更新的图片数；RTX 3060 的安全值需按实际显存测得。|
|Confidence Threshold|保留预测的最低置信度；阈值越低通常召回越高但误报也更多。|
|Precision|被报告为某类的目标中，真实正确的比例；低 Precision 会把特效误认为怪/loot。|
|Recall|真实目标中被检出的比例；低 Recall 会错误地看成清怪或未发现 loot。|
|False Positive|不存在的怪/loot 被报出。|
|False Negative|真实玩家、怪物或 loot 未检出。|
|Inference（推理）|运行期把一帧 ROI 输入模型并得到检测框的过程。|

训练必须覆盖玩家的站立、走路、攻击、瞬移、跳跃等动画：精灵帧、姿态、特效遮挡和框大小都变化。怪物也应覆盖奔跑、跳跃、受击、遮挡、重叠及死亡前后，否则模型可能只认识静态“典型帧”。

连续视频的相邻帧高度相似；若随机把同一段录像的相邻帧分入训练和测试，测试画面几乎等于模型已见画面，导致指标虚高。应以录像会话/地图时段为分组边界，并在新会话上测试。
