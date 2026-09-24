"""只使用 pydirectinput 的安全输入封装；DEBUG_MODE 时完全不发键。"""
from __future__ import annotations
import atexit, logging, time
import config
LOG=logging.getLogger(__name__)
try: import pydirectinput
except ImportError: pydirectinput=None
class KeyboardController:
 def __init__(self, enabled: bool = not config.DEBUG_MODE): self.enabled=enabled; self.down:set[str]=set(); atexit.register(self.release_all_keys)
 def _down(self,key):
  if key not in self.down:
   if self.enabled and pydirectinput: pydirectinput.keyDown(key)
   self.down.add(key)
 def _up(self,key):
  if key in self.down:
   if self.enabled and pydirectinput: pydirectinput.keyUp(key)
   self.down.discard(key)
 def move_left(self): self._up(config.RIGHT_KEY); self._down(config.LEFT_KEY)
 def move_right(self): self._up(config.LEFT_KEY); self._down(config.RIGHT_KEY)
 def stop_movement(self): self._up(config.LEFT_KEY); self._up(config.RIGHT_KEY)
 def move_pulse(self, direction:str):
  (self.move_left if direction == "left" else self.move_right)(); time.sleep(config.MOVE_PULSE_SECONDS); self.stop_movement()
 def attack_start(self): self.stop_movement(); self._down(config.ATTACK_KEY)
 def attack_stop(self): self._up(config.ATTACK_KEY)
 def emergency_pressed(self) -> bool:
  """轮询 F8；Windows 不可用时安全地返回 False。"""
  try:
   import win32api, win32con
   return bool(win32api.GetAsyncKeyState(win32con.VK_F8) & 0x8000)
  except (ImportError, AttributeError): return False
 def release_all_keys(self):
  for key in list(self.down): self._up(key)
  LOG.info("已释放所有按键")
