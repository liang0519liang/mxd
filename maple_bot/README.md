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
python main.py auto --enable-input # 自动状态机并明确启用 pydirectinput 输入
# 或在 config.py 设置 DEBUG_MODE = False 后运行：python main.py auto
```

在 `config.py` 填写精确的 `WINDOW_TITLE_KEYWORD`，并保持其客户区为 1366×768。`preview` 与 `detect` 是只读模式：窗口可见即可，不要求前台焦点；`auto` 模式要求游戏窗口获得焦点，否则会暂停并释放按键。若匹配多个窗口，程序会拒绝选择；真正最小化、尺寸异常或 ROI 越界都会停止控制。DPI 缩放造成偏移时，请优先使用 100% 缩放；程序已尝试设置进程 DPI 感知。

## 模板与 ROI

1. 从**客户区**截图裁剪怪物，保存 PNG/JPG/JPEG/BMP 到 `templates/monsters/`；同怪不同动画分别保存。PNG 格式本身没有影响，但模板白色背景必须与 ROI 中的实际背景相近；若白色底来自截图工具的透明区域填充，匹配分数通常会很低。
2. 裁剪角色主体到 `templates/player/`，建议分别提供站立、左右移动、攻击等姿态。`detect` 顶部的 `player found`、`player_best` 会显示人物是否达到 `PLAYER_MATCH_THRESHOLD`；人物命中后以橙色框和红色脚底点标出。自动模式缺失此模板会拒绝启动。
3. 先运行 `preview`，根据蓝色矩形调整 `ROI_LEFT/TOP/WIDTH/HEIGHT`；ROI 坐标相对客户区左上角，必须完全在 1366×768 内。
4. 用 `detect` 观察绿色框、顶部 `monsters` 计数、`best` 最高分和每个模板的 `template max`。绿色框只会在分数达到 `MATCH_THRESHOLD` 后出现；若 `best` 低于阈值，请先检查模板是否从同一客户区分辨率裁剪，再逐步下调阈值。检测结果已转换为客户区坐标。
5. 自动模式默认**拒绝启动输入**，避免误操作。确认检测框稳定后，运行 `python main.py auto --enable-input`，或将 `DEBUG_MODE=False` 后运行 `python main.py auto`。终端必须显示“游戏输入已启用”；若显示“游戏输入未启用”，程序不会调用键盘接口。先手工测试 `pydirectinput` 是否能被游戏接收；兼容性无法保证。

## 配置速查

`WINDOW_*`/`EXPECTED_CLIENT_*` 控制窗口校验；`ROI_*` 为平台监测区域；`MONSTER_THRESHOLD` 是进入寻怪门槛，`EMPTY_CONFIRM_FRAMES` 是清场确认（攻击中只要仍有一只可靠怪物就持续）；`DETECTION_CONFIRM_FRAMES` 降低触发抖动；`PLAYER_MATCH_THRESHOLD` 控制人物定位；`LEFT_KEY/RIGHT_KEY/ATTACK_KEY`、`ATTACK_DISTANCE`、`MOVE_PULSE_SECONDS`、`MOVE_TIMEOUT_SECONDS` 控制操作；三个 `*_INTERVAL` 是轮询间隔；`EMERGENCY_STOP_KEY` 保留为 F8 配置，`DEBUG_MODE/SAVE_DEBUG_IMAGES/MAX_CONSECUTIVE_DETECTION_FAILURES` 为安全调试项。F8 使用 Win32 `GetAsyncKeyState` 轮询；请在实际 Windows 部署时验证。窗口异常和 Ctrl+C 已立即释放按键。

## 排查

- “没有模板”：检查图片扩展名与目录、读取权限和 OpenCV 能否打开该文件。
- “客户区尺寸异常/ROI 超界”：不要用窗口外框尺寸，按预览重新配置；检查显示缩放。
- “窗口未获得焦点”：仅 `auto` 要求前台焦点；手动点击游戏窗口，程序宁可停止也不会盲按。
- 自动模式没有移动/攻击：先检查终端是否有“游戏输入已启用”。若没有，请使用 `python main.py auto --enable-input` 或设置 `DEBUG_MODE=False`；之后用记事本等安全窗口单独验证 `pydirectinput` 的方向键和攻击键是否被系统接收。
- 人物定位失败：确认图片放在 `templates/player/` 而不是怪物目录；先运行 `detect` 查看 `player_best`。人物模板必须来自同一客户区和 DPI，且应包含角色主体与少量真实背景；至少添加站立、移动、攻击多个动画帧。若 `player_best` 低于 `PLAYER_MATCH_THRESHOLD`，每次仅下调 `0.05` 后复测，避免误把怪物当人物。
- detect 没有绿色框：先看顶部 `best` 与 `template max`。这不是程序未检测，而是当前最高分未达到阈值；确保模板不是纯色、来自同一 1366×768 客户区和相同 DPI，然后逐步下调 `MATCH_THRESHOLD`。PNG 没有问题，但白底若与游戏实际背景不同会严重拉低分数；请重新裁剪包含真实游戏背景的模板，避免透明像素被白色填充。
- F8 紧急停止由 Win32 轮询实现；实际 Windows 部署前请确认其能被可靠接收。退出程序使用 Ctrl+C，`finally`/`atexit` 会释放按键。
