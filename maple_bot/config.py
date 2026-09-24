"""MapleStory Vision Bot 的唯一用户配置文件。所有时间单位均为秒。"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "templates" / "monsters"
PLAYER_TEMPLATE_DIR = BASE_DIR / "templates" / "player"
DEBUG_DIR = BASE_DIR / "debug"
LOG_DIR = BASE_DIR / "logs"

WINDOW_TITLE_KEYWORD = "MapleStory"
WINDOW_MODE = "client"  # 当前仅支持 client：Win32 客户区坐标
EXPECTED_CLIENT_WIDTH = 1366
EXPECTED_CLIENT_HEIGHT = 768
ROI_LEFT, ROI_TOP, ROI_WIDTH, ROI_HEIGHT = 0, 300, 1366, 400

MONSTER_THRESHOLD = 3
MATCH_THRESHOLD = 0.72  # 从 detect 模式显示的最高分开始校准
MONSTER_MIN_DISTANCE = 36
EMPTY_CONFIRM_FRAMES = 3
DETECTION_CONFIRM_FRAMES = 2
PLAYER_MATCH_THRESHOLD = 0.65  # 人物动画变化较大；用 detect 顶部 player_best 再校准

LEFT_KEY, RIGHT_KEY, ATTACK_KEY = "left", "right", "ctrl"
ATTACK_DISTANCE = 130
MOVE_PULSE_SECONDS = 0.12
MOVE_TIMEOUT_SECONDS = 8.0
IDLE_INTERVAL, APPROACH_INTERVAL, ATTACK_INTERVAL = 0.30, 0.12, 0.15

EMERGENCY_STOP_KEY = "f8"
DEBUG_MODE = True             # 调试模式默认不向游戏发送输入
SAVE_DEBUG_IMAGES = False
MAX_CONSECUTIVE_DETECTION_FAILURES = 5

SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp"}
