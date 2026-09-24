from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import logging,time
import config
from detector import Detection, DetectionResult
LOG=logging.getLogger(__name__)
class State(Enum): IDLE="IDLE"; APPROACH="APPROACH"; ATTACK="ATTACK"; RECOVER="RECOVER"
@dataclass
class Observation:
 monsters: DetectionResult; player: Detection|None; window_ok:bool=True; emergency:bool=False
class BotStateMachine:
 def __init__(self, controller): self.controller=controller; self.state=State.IDLE; self.empty_frames=0; self.confirm_frames=0; self.approach_started=None; self.reason=""
 def transition(self, state:State, reason:str):
  if state != self.state: LOG.info("状态 %s -> %s：%s",self.state.value,state.value,reason)
  self.state=state; self.reason=reason
  if state in (State.IDLE,State.RECOVER): self.controller.release_all_keys()
  if state == State.APPROACH: self.approach_started=time.monotonic()
 def step(self,o:Observation):
  if o.emergency or not o.window_ok: self.transition(State.RECOVER,"F8 紧急停止" if o.emergency else "窗口不可用或失焦"); return self.state
  if not o.monsters.reliable: self.transition(State.RECOVER,o.monsters.error or "怪物检测不可靠"); return self.state
  count=len(o.monsters.detections)
  if self.state==State.RECOVER: self.transition(State.IDLE,"视觉与窗口恢复"); return self.state
  if self.state==State.IDLE:
   self.confirm_frames=self.confirm_frames+1 if count>=config.MONSTER_THRESHOLD else 0
   if self.confirm_frames>=config.DETECTION_CONFIRM_FRAMES: self.transition(State.APPROACH,"达到怪物触发阈值")
  elif self.state==State.APPROACH:
   if count==0: self.transition(State.IDLE,"怪物已消失"); return self.state
   if o.player is None: self.transition(State.RECOVER,"人物定位失败"); return self.state
   if time.monotonic()-(self.approach_started or time.monotonic())>config.MOVE_TIMEOUT_SECONDS: self.transition(State.RECOVER,"移动超时"); return self.state
   target=sum(d.x for d in o.monsters.detections)/count; distance=target-o.player.x
   if abs(distance)<=config.ATTACK_DISTANCE: self.controller.stop_movement(); self.controller.attack_start(); self.empty_frames=0; self.transition(State.ATTACK,"进入攻击距离")
   else: self.controller.move_pulse("right" if distance>0 else "left")
  elif self.state==State.ATTACK:
   if o.player is None: self.transition(State.RECOVER,"攻击中人物定位失败"); return self.state
   if count: self.empty_frames=0
   else: self.empty_frames+=1
   if self.empty_frames>=config.EMPTY_CONFIRM_FRAMES: self.controller.attack_stop(); self.transition(State.IDLE,"连续确认无怪")
  return self.state
