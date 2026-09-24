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
