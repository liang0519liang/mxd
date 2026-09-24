import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
import config
from detector import Detection,DetectionResult
from state_machine import *
class C:
 def __init__(s): s.calls=[]
 def __getattr__(s,n): return lambda *a:s.calls.append(n)
def obs(n,player=True,ok=True,emergency=False): return Observation(DetectionResult([Detection(100+i*20,100,.9,'x') for i in range(n)],True),Detection(0,0,.9,'p') if player else None,ok,emergency)
def test_transitions(monkeypatch):
 monkeypatch.setattr(config,'DETECTION_CONFIRM_FRAMES',1); c=C(); f=BotStateMachine(c); assert f.step(obs(3))==State.APPROACH; assert f.step(obs(3))==State.ATTACK
def test_attack_keeps_when_below_threshold(monkeypatch):
 monkeypatch.setattr(config,'DETECTION_CONFIRM_FRAMES',1); c=C(); f=BotStateMachine(c); f.step(obs(3)); f.step(obs(3)); assert f.step(obs(1))==State.ATTACK
def test_empty_and_safety(monkeypatch):
 monkeypatch.setattr(config,'EMPTY_CONFIRM_FRAMES',2); c=C(); f=BotStateMachine(c); f.state=State.ATTACK; f.step(obs(0)); assert f.state==State.ATTACK; f.step(obs(0)); assert f.state==State.IDLE; f.state=State.APPROACH; f.step(obs(3,False)); assert f.state==State.RECOVER; f.step(obs(3,ok=False)); assert f.state==State.RECOVER and 'release_all_keys' in c.calls
def test_emergency_releases():
 c=C(); f=BotStateMachine(c); f.step(obs(3,emergency=True)); assert f.state==State.RECOVER and 'release_all_keys' in c.calls
