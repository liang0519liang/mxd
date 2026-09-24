"""只使用 pydirectinput 的安全输入封装；不注入或修改游戏进程。"""
from __future__ import annotations

import atexit
import logging
import time

import config

LOG = logging.getLogger(__name__)
try:
    import pydirectinput
except ImportError:
    pydirectinput = None


class KeyboardController:
    def __init__(self, enabled: bool = False):
        if enabled and pydirectinput is None:
            raise RuntimeError("已请求发送游戏输入，但 pydirectinput 未安装；请执行 pip install -r requirements.txt")
        self.enabled = enabled
        self.down: set[str] = set()
        if self.enabled:
            # pydirectinput 的默认全局暂停会让短脉冲明显变长。
            pydirectinput.PAUSE = 0
            LOG.warning("游戏输入已启用：方向键=%s/%s，攻击键=%s", config.LEFT_KEY, config.RIGHT_KEY, config.ATTACK_KEY)
        else:
            LOG.warning("游戏输入未启用：不会调用 keyDown/keyUp")
        atexit.register(self.release_all_keys)

    def _down(self, key: str) -> None:
        if key in self.down:
            return
        if self.enabled:
            pydirectinput.keyDown(key)
            LOG.debug("keyDown(%s)", key)
        self.down.add(key)

    def _up(self, key: str) -> None:
        if key not in self.down:
            return
        if self.enabled:
            pydirectinput.keyUp(key)
            LOG.debug("keyUp(%s)", key)
        self.down.discard(key)

    def move_left(self) -> None:
        self._up(config.RIGHT_KEY)
        self._down(config.LEFT_KEY)

    def move_right(self) -> None:
        self._up(config.LEFT_KEY)
        self._down(config.RIGHT_KEY)

    def stop_movement(self) -> None:
        self._up(config.LEFT_KEY)
        self._up(config.RIGHT_KEY)

    def move_pulse(self, direction: str) -> None:
        (self.move_left if direction == "left" else self.move_right)()
        time.sleep(config.MOVE_PULSE_SECONDS)
        self.stop_movement()

    def teleport(self, direction: str) -> None:
        """短按瞬移键并同时按方向；无论异常与否都释放两个键。"""
        if not config.TELEPORT_ENABLED:
            self.move_pulse(direction)
            return
        self.stop_movement()
        movement_key = config.LEFT_KEY if direction == "left" else config.RIGHT_KEY
        try:
            self._down(config.TELEPORT_KEY)
            self._down(movement_key)
            time.sleep(config.TELEPORT_PULSE_SECONDS)
        finally:
            self._up(movement_key)
            self._up(config.TELEPORT_KEY)

    def attack_start(self) -> None:
        self.stop_movement()
        self._down(config.ATTACK_KEY)

    def attack_stop(self) -> None:
        self._up(config.ATTACK_KEY)

    def emergency_pressed(self) -> bool:
        """轮询可配置的 F8；Windows 不可用时安全地返回 False。"""
        try:
            import win32api
            return bool(win32api.GetAsyncKeyState(0x77) & 0x8000)  # VK_F8
        except ImportError:
            return False

    def release_all_keys(self) -> None:
        for key in list(self.down):
            self._up(key)
        LOG.info("已释放所有按键")
