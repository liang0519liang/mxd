# MapleStory Vision Bot

> 面向 Windows 11 的本地视觉实验工具：用 Win32 客户区截图、OpenCV 多模板匹配与有限状态机监测同层平台。它不包含游戏素材，不注入进程、不修改内存、不绕过反作弊；在线游戏自动化可能违反运营规则或导致账号处罚，请先确认适用规则并自行承担风险。

## 已实现与待验证

已实现：客户区/ROI 校验、多个模板加载与去重、人物脚底参考点、调试预览、按键安全封装、`IDLE/APPROACH/ATTACK/RECOVER` 状态机及不依赖游戏窗口的单元测试。**未使用真实截图验证识别率，也未验证目标游戏是否接受 `pydirectinput` 输入。**模板匹配仅适合外观、缩放和背景相对稳定的场景；动画、遮挡、特效、DPI 或模板差异会造成漏检/误检，应补充多姿态模板并调参。

## 架构与目录

- `capture.py`：Win32 客户区（非标题栏）定位、DPI 感知和 mss 截图。
- `detector.py`：模板管理、匹配、距离 NMS、人物/怪物坐标与绘制。
- `controller.py`：短脉冲方向键、长按攻击、退出释放按键；调试模式不会发键。
- `state_machine.py`：安全 FSM；检测不可靠、失焦、移动超时均进入恢复。
- `config.py`：唯一配置入口；`templates/monsters/`、`templates/player/` 分别存放模板，`debug/` 与 `logs/` 存放输出。

## Windows 11 准备与启动

```powershell
cd maple_bot
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q
python main.py preview     # 实时客户区 + ROI 预览，q/ESC 退出
python main.py detect      # 纯视觉检测，不发送输入
python main.py auto        # 自动状态机；仍需将 config.DEBUG_MODE 改为 False 才发送输入
```

在 `config.py` 填写精确的 `WINDOW_TITLE_KEYWORD`，将窗口置前并保持其客户区为 1366×768。若匹配多个窗口，程序会拒绝选择；最小化、失焦、尺寸异常或 ROI 越界都会停止控制。DPI 缩放造成偏移时，请优先使用 100% 缩放；程序已尝试设置进程 DPI 感知。

## 模板与 ROI

1. 从**客户区**截图裁剪怪物，保存 PNG/JPG/JPEG/BMP 到 `templates/monsters/`；同怪不同动画分别保存。
2. 裁剪角色主体到 `templates/player/`，建议提供站立/移动/攻击姿态；自动模式缺失此模板会拒绝启动。
3. 先运行 `preview`，根据蓝色矩形调整 `ROI_LEFT/TOP/WIDTH/HEIGHT`；ROI 坐标相对客户区左上角，必须完全在 1366×768 内。
4. 用 `detect` 观察绿色框、置信度与计数，调整 `MATCH_THRESHOLD`、`MONSTER_MIN_DISTANCE`。检测结果已转换为客户区坐标。
5. 在空闲环境运行 `auto` 且保持 `DEBUG_MODE=True` 检查状态；确认后改为 `False`。先手工测试 `pydirectinput` 是否能被游戏接收；兼容性无法保证。

## 配置速查

`WINDOW_*`/`EXPECTED_CLIENT_*` 控制窗口校验；`ROI_*` 为平台监测区域；`MONSTER_THRESHOLD` 是进入寻怪门槛，`EMPTY_CONFIRM_FRAMES` 是清场确认（攻击中只要仍有一只可靠怪物就持续）；`DETECTION_CONFIRM_FRAMES` 降低触发抖动；`PLAYER_MATCH_THRESHOLD` 控制人物定位；`LEFT_KEY/RIGHT_KEY/ATTACK_KEY`、`ATTACK_DISTANCE`、`MOVE_PULSE_SECONDS`、`MOVE_TIMEOUT_SECONDS` 控制操作；三个 `*_INTERVAL` 是轮询间隔；`EMERGENCY_STOP_KEY` 保留为 F8 配置，`DEBUG_MODE/SAVE_DEBUG_IMAGES/MAX_CONSECUTIVE_DETECTION_FAILURES` 为安全调试项。F8 使用 Win32 `GetAsyncKeyState` 轮询；请在实际 Windows 部署时验证。窗口异常和 Ctrl+C 已立即释放按键。

## 排查

- “没有模板”：检查图片扩展名与目录、读取权限和 OpenCV 能否打开该文件。
- “客户区尺寸异常/ROI 超界”：不要用窗口外框尺寸，按预览重新配置；检查显示缩放。
- “窗口未获得焦点”：手动点击游戏窗口，程序宁可停止也不会盲按。
- 漏检/重复：增加对应动画模板、提高/降低阈值并调整最小间距；不要把检测失败误当作无怪。
- F8 紧急停止由 Win32 轮询实现；实际 Windows 部署前请确认其能被可靠接收。退出程序使用 Ctrl+C，`finally`/`atexit` 会释放按键。
