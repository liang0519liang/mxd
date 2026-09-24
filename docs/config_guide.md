# `config.py` 完整设计（拟定接口，Phase 0）

后续的 `config.py` 是唯一关键可调参数来源；业务模块不得私藏阈值或键位。以下为拟实施的带中英文注释示例。默认值是**安全启动/占位值**，并非游戏已标定事实；凡标注“实测”的项必须经 UI 与录像测试校准。

```python
# config.py — planned, not executable in Phase 0
# ===== Game window / 游戏窗口 =====
GAME_WINDOW_TITLE = "MapleStory"  # 中文：窗口标题关键字；English: title substring. Unit: text; verify actual title.
EXPECTED_CLIENT_WIDTH = 1366  # 中文：期望客户区宽度；English: expected client width. Unit: px; mismatch warns, not assumed valid.
EXPECTED_CLIENT_HEIGHT = 768  # 中文：期望客户区高度；English: expected client height. Unit: px; mismatch warns, not assumed valid.
REQUIRE_GAME_FOCUS = True  # 中文：要求窗口前台；English: require foreground. Unit: bool; False only after risk review.
WINDOW_CHECK_INTERVAL_S = 0.5  # 中文：窗口复查间隔；English: window validation period. Unit: s; tune 0.2–2.0.
CAPTURE_FPS_LIMIT = 30  # 中文：采集上限；English: capture FPS cap. Unit: FPS; tune from measured load.

# ===== ROI / 战斗区域（相对客户区） =====
ROI_X = 0  # 中文：ROI 左上 X；English: ROI x relative to client. Unit: px; must be measured.
ROI_Y = 0  # 中文：ROI 左上 Y；English: ROI y relative to client. Unit: px; must be measured.
ROI_WIDTH = 1366  # 中文：ROI 宽；English: ROI width. Unit: px; must stay in client bounds.
ROI_HEIGHT = 768  # 中文：ROI 高；English: ROI height. Unit: px; must stay in client bounds.

# ===== YOLO / 目标检测 =====
MODEL_PATH = "models/best.pt"  # 中文：模型路径；English: trained model path. Unit: path; map/character/model combination must match.
DETECTION_CONFIDENCE = 0.35  # 中文：全局最低置信度；English: global minimum confidence. Unit: 0–1; tune validation + live false positives.
PLAYER_CONFIDENCE = 0.50  # 中文：玩家阈值；English: player confidence threshold. Unit: 0–1; tune from validation.
MONSTER_CONFIDENCE = 0.40  # 中文：怪物阈值；English: monster confidence threshold. Unit: 0–1; tune from validation.
LOOT_CONFIDENCE = 0.40  # 中文：掉落物阈值；English: loot confidence threshold. Unit: 0–1; tune from validation.
INFERENCE_IMAGE_SIZE = 640  # 中文：推理缩放边长；English: inference image size. Unit: px; 416–640 first trial.
INFERENCE_INTERVAL_S = 0.05  # 中文：推理最小间隔；English: inference minimum period. Unit: s; must follow measured latency.
DEVICE = "cuda:0"  # 中文：推理设备；English: inference device. Unit: torch device; fallback must be explicit.
MAX_MISSED_FRAMES = 5  # 中文：玩家最大连续漏检帧；English: maximum missed player frames. Unit: frames; calibrate to FPS/occlusion.

# ===== Keys / 按键（禁止业务模块硬编码） =====
MOVE_LEFT_KEY = "left"  # 中文：左移；English: move left key. Unit: input-library key name; user verifies.
MOVE_RIGHT_KEY = "right"  # 中文：右移；English: move right key. Unit: key name; user verifies.
ATTACK_KEY = ""  # 中文：攻击键；English: attack key. Unit: key name; blank disables real use until confirmed.
TELEPORT_KEY = ""  # 中文：瞬移键；English: teleport key. Unit: key name; separate from direction.
BUFF_KEY = ""  # 中文：Buff 键；English: buff key. Unit: key name; separate from attack.
EMERGENCY_STOP_KEY = "f8"  # 中文：急停键；English: emergency-stop key. Unit: key name; test outside game first.
PAUSE_RESUME_KEY = "f7"  # 中文：暂停/恢复；English: pause-resume key. Unit: key name; user configurable.

# ===== Movement and teleport / 移动与瞬移 =====
MOVE_PULSE_DURATION_S = 0.10  # 中文：移动短按；English: movement pulse duration. Unit: s; measure, 0.03–0.30.
TELEPORT_PULSE_DURATION_S = 0.05  # 中文：瞬移短按；English: teleport pulse duration. Unit: s; measure skill semantics.
TELEPORT_COOLDOWN_S = 0.0  # 中文：瞬移冷却；English: teleport cooldown. Unit: s; MUST be measured.
POST_TELEPORT_SETTLE_TIME_S = 0.25  # 中文：瞬移后稳定等待；English: settle delay. Unit: s; measure animation/network.
MOVE_RECHECK_INTERVAL_S = 0.10  # 中文：移动后复检；English: recheck delay. Unit: s; tune to actual detection latency.
MAX_CONSECUTIVE_TELEPORTS = 1  # 中文：连续瞬移上限；English: consecutive teleport cap. Unit: count; conservative safety default.
APPROACH_DISTANCE_PX = 200  # 中文：考虑接近的距离；English: approach distance. Unit: ROI px; placeholder, calibrate.
ATTACK_DISTANCE_PX = 80  # 中文：攻击距离；English: attack distance. Unit: ROI px; MUST be measured per skill.
MAX_APPROACH_TIME_S = 8.0  # 中文：接近总超时；English: max approach time. Unit: s; safety limit, tune.
MAX_MOVEMENT_ATTEMPTS = 12  # 中文：移动尝试上限；English: movement attempt cap. Unit: count; safety limit.

# ===== Attack / 攻击 =====
ATTACK_TRIGGER_MONSTER_COUNT = 1  # 中文：触发攻击的稳定怪物数；English: monster-count trigger. Unit: count; user policy, e.g. 3.
ATTACK_HOLD_DURATION_S = 0.15  # 中文：单次攻击保持；English: attack hold duration. Unit: s; measure input behavior.
ATTACK_RECHECK_INTERVAL_S = 0.10  # 中文：攻击复检间隔；English: attack recheck interval. Unit: s.
ATTACK_CLEAR_CONFIRM_FRAMES = 3  # 中文：清空确认帧；English: clear confirmation frames. Unit: frames; tune against false negatives.
ATTACK_MAX_DURATION_S = 10.0  # 中文：攻击超时；English: maximum attack duration. Unit: s; safety limit.
ATTACK_SETTLE_DELAY_S = 0.10  # 中文：攻击前稳定延迟；English: pre-attack settle delay. Unit: s.

# ===== Buff / 增益 =====
BUFF_ENABLED = False  # 中文：是否启用；English: enable buffs. Unit: bool; default off until key and rules confirmed.
BUFF_INTERVAL_S = 120.0  # 中文：施放周期；English: cast interval. Unit: s; placeholder, MUST be skill-tested.
BUFF_HOLD_DURATION_S = 0.10  # 中文：按住时长；English: buff hold duration. Unit: s; measure.
BUFF_CAST_DELAY_S = 0.30  # 中文：施放后等待；English: post-cast delay. Unit: s; measure.
BUFF_RETRY_COUNT = 1  # 中文：最大重试；English: maximum retries. Unit: count; finite only.
BUFF_RETRY_INTERVAL_S = 1.0  # 中文：重试间隔；English: retry interval. Unit: s.

# ===== Loot / 掉落物与宠物 =====
LOOT_PASS_DISTANCE_PX = 45  # 中文：经过判定距离；English: loot pass distance. Unit: ROI px; MUST be measured.
LOOT_DWELL_TIME_S = 2.0  # 中文：附近停留；English: dwell near loot. Unit: s; user example, validate pet behavior.
LOOT_VERIFY_TIMEOUT_S = 3.0  # 中文：消失验证超时；English: visual verification timeout. Unit: s; tune to detection stability.
LOOT_MAX_ATTEMPTS = 2  # 中文：单物品最大尝试；English: per-loot attempt cap. Unit: count; finite.
LOOT_QUEUE_TIMEOUT_S = 20.0  # 中文：队列总超时；English: queue timeout. Unit: s; safety limit.

# ===== Debug / 调试 =====
DEBUG_MODE = True  # 中文：调试模式；English: debug mode. Unit: bool.
DRY_RUN = True  # 中文：只显示决策不发键；English: log decisions, send no input. Unit: bool; safe default.
SHOW_DETECTION_BOXES = True  # 中文：显示检测框；English: show boxes. Unit: bool.
SHOW_ROI = True  # 中文：显示 ROI；English: show ROI. Unit: bool.
SHOW_PLAYER_COORDINATES = True  # 中文：显示玩家坐标；English: show player coordinates. Unit: bool.
SHOW_MONSTER_COORDINATES = True  # 中文：显示怪物坐标；English: show monster coordinates. Unit: bool.
SHOW_LOOT_COORDINATES = True  # 中文：显示掉落物坐标；English: show loot coordinates. Unit: bool.
SHOW_FSM_STATE = True  # 中文：显示状态机；English: show FSM state. Unit: bool.
SAVE_DEBUG_FRAMES = False  # 中文：保存调试帧；English: save debug frames. Unit: bool; disk-sensitive.
LOG_LEVEL = "INFO"  # 中文：日志级别；English: log level. Unit: logging level; DEBUG for calibration.
```

## 参数标定原则

所有 `*_PX` 只在**同一 ROI 分辨率**中有意义。通过 Overlay 记录“脚点差—操作—复检脚点差”，而非猜测游戏世界单位。先标定检测正确性，再标定普通移动，再标定攻击距离，最后单独标定瞬移；每次只改一个参数并保存截图/日志。Buff 的周期、按键与是否允许输入自动化必须由用户确认。

Buff 调度器使用 `time.monotonic()` 独立维护到期标志：攻击循环的循环时间随怪物、推理负载和异常而变化，`sleep(BUFF_INTERVAL)` 会阻塞检测、错过急停、使周期漂移，也无法和瞬移/攻击进行资源仲裁。
