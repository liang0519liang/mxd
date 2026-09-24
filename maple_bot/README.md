# MapleStory Vision Bot（YOLO 版）

本项目使用**本地 YOLO 模型**识别 `player`、`monster` 和 `drop`，再以有限状态机执行短脉冲左右移动、可选瞬移、攻击与安全恢复。它不注入进程、不读取/修改内存、不提供绕过反作弊的方法。在线游戏自动化可能违反运营规则并导致账号处罚，请仅在获准环境中使用。

> 每个 `best.pt` 代表一个“角色外观 + 怪物 + 地图/分辨率”的配置。项目不附带游戏截图、视频、数据集或训练权重，也不声称已在真实游戏中验证。

## 训练工作流

1. 录制指定地图、指定角色打怪的视频；抽取包含站立、移动、攻击、受遮挡、不同怪物数量与掉落物的帧。
2. 在 CVAT、LabelImg 或 Roboflow 中人工标注三个类别，**类别名称必须严格为** `player`、`monster`、`drop`。掉落物只可视化，不会被当作攻击目标。
3. 导出 YOLO Detection 格式，建立 `dataset/data.yaml`，其 `train`、`val` 指向图片目录，`names: [player, monster, drop]`。详细说明在 `dataset/README.md`。
4. 安装依赖后训练：
   ```powershell
   cd maple_bot
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python train.py --data dataset/data.yaml --model yolo11n.pt --epochs 100 --imgsz 960 --device 0
   ```
5. 将训练输出 `runs/maple/weights/best.pt` 复制为 `models/maple_yolo.pt`，或在 `config.py` 修改 `YOLO_MODEL_PATH`。先使用验证集与真实 `detect` 模式检查漏检/误检，再考虑自动控制。

## 运行

```powershell
python main.py preview                 # 客户区、ROI 与 YOLO 检测预览；q/ESC 退出
python main.py detect                  # 纯视觉模式，不发送输入
python main.py auto --enable-input     # 显式允许 pydirectinput 输入
# 或将 config.DEBUG_MODE = False 后：python main.py auto
```

窗口标题在 `WINDOW_TITLE_KEYWORD` 配置。`preview`/`detect` 是只读截图，窗口可见即可；`auto` 要求游戏窗口获得前台焦点，否则释放按键。客户区必须为 1366×768，蓝框 ROI 是参与怪物决策的区域；人物可以在全客户区识别。

## 控制逻辑与防呆

- 每帧从 ROI 中选取离角色水平距离最近的 `monster`；`drop` 不参与决策。
- 距离大于 `TELEPORT_DISTANCE` 时，短按 `TELEPORT_KEY + 左/右键`；否则短脉冲移动。进入 `ATTACK_DISTANCE` 后先释放方向键，再长按 `ATTACK_KEY`。
- ROI 连续无怪时会释放攻击并回到 `IDLE`；`EMPTY_CONFIRM_FRAMES` 用于避免单帧漏检误停。`NO_MONSTER_WAIT_SECONDS` 是无怪等待配置；可按地图刷新时间设置为 2 秒。
- 人物/怪物 YOLO 推理失败、窗口失焦、窗口最小化、移动超时或 F8 紧急停止时，状态机进入 `RECOVER` 并释放所有按键。
- `auto` 未传 `--enable-input` 且 `DEBUG_MODE=True` 时会明确拒绝启动，不会静默“假按键”。终端应出现“游戏输入已启用”。

## 关键配置

所有参数都在 `config.py`：`YOLO_MODEL_PATH`、`YOLO_CONFIDENCE`、`YOLO_IOU_THRESHOLD`、类别名、ROI、`ATTACK_DISTANCE`、`TELEPORT_*`、按键、检测间隔、`DEBUG_MODE`。先通过 `detect` 查看绿色怪物框、橙色角色框和青色掉落物框，确认稳定后再调低置信度或打开输入。不要为了提升召回率无限降低 `YOLO_CONFIDENCE`，否则可能向误检目标移动。

## 真实环境待验证

需在实际 Windows 游戏环境验证：YOLO 模型对当前地图的精度、`pydirectinput` 对目标游戏的兼容性、瞬移键组合和攻击键。若游戏不接受模拟输入，项目不会也不应尝试使用注入、内存修改、DLL 或规避反作弊的替代方案。

## 从已录制视频到实施的完整流程

以下命令均在 `maple_bot/` 目录执行。网页标注服务仅绑定 `127.0.0.1`，不会向局域网公开，也不会上传视频或标签。

### 1. 抽帧

```powershell
python extract_frames.py "D:\videos\maple_map_a.mp4" --every-seconds 0.5 --max-frames 1500
```

`--every-seconds 0.5` 适合先建立基础数据集；动作很快或怪物动画差异大时调至 `0.2~0.3`。检查 `dataset/raw_frames/`，删除黑屏、菜单、加载页和大量近乎重复帧。请保留无怪物、无角色或只有掉落物的少量画面作为负样本。

### 2. 启动本地网页手动标注

```powershell
python label_server.py
```

在浏览器打开 **http://127.0.0.1:5000**。网页提供：鼠标拖动框选，分类下拉框，`1/2/3` 快捷键选择 `player/monster/drop`，`S` 保存，`A/D` 切换帧，撤销按钮。每一帧（包括没有任何目标的帧）都必须点击保存；保存后的标签在 `dataset/labels/`。标注框应紧贴可见目标主体，不要把大块纯背景、姓名条或 UI 一起框入。

### 3. 检查、划分数据集与生成 data.yaml

```powershell
python prepare_dataset.py --val-ratio 0.2
```

该脚本会拒绝继续处理任何尚未保存标注的图片，使用固定随机种子生成 `dataset/yolo/images/{train,val}`、对应标签和 `dataset/yolo/data.yaml`。先随机打开一些 train 与 val 图片、核对框和类别，避免类号颠倒或漏标。

### 4. 训练每张地图/角色配置

```powershell
python train.py --data dataset/yolo/data.yaml --model yolo11n.pt --epochs 100 --imgsz 960 --device 0
```

无 NVIDIA CUDA GPU 时将 `--device 0` 改为 `--device cpu`，训练会明显更慢。首次训练需要 Ultralytics 下载预训练权重；如网络受限，请预先把相应 `.pt` 文件放在本地并通过 `--model` 指定。训练产物位于 `runs/maple/weights/best.pt`。将它复制到 `models/maple_yolo.pt`，或更新 `YOLO_MODEL_PATH`，即得到这张地图的独立配置。

### 5. 离线验证，再进行实时 detect

```powershell
python validate.py --model runs/maple/weights/best.pt --data dataset/yolo/data.yaml --source "D:\videos\maple_map_a.mp4" --device 0
python main.py detect
```

`validate.py` 输出 mAP50-95/mAP50，并将带框视频输出到 `runs/validate_video/`。必须人工观看该视频，重点查看人物被遮挡、攻击特效、怪物重叠、掉落物密集与无怪刷新阶段；mAP 不能替代这种检查。`detect` 实时模式确认绿色怪物框和橙色人物框稳定之后，才继续。

### 6. 受控实施

1. 在 `config.py` 选择这张地图对应的 `YOLO_MODEL_PATH`，校准 `ROI_*`、攻击键、瞬移键、攻击距离和瞬移距离。
2. 先运行 `python main.py detect`，确认 ROI 里的绿色怪物数量、橙色人物位置和蓝色 ROI 正确。
3. 在安全地图、角色静止且游戏窗口前台时，运行 `python main.py auto --enable-input`。
4. 保持可随时按下 F8；确认每次普通移动、瞬移、攻击和无怪两秒等待符合预期。任何框漂移、误检、窗口失焦或人物丢失时应停止，补充对应视频帧、重新标注和训练，而不是无限降低 YOLO 阈值。

真实游戏输入兼容性、瞬移组合键，以及模型在未见过的地图/怪物上的效果仍需由你在本机验证。
