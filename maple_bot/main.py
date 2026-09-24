from __future__ import annotations
import argparse, logging, time
from pathlib import Path
import cv2
import config
from capture import GameCapture, CaptureError
from detector import load_monster_templates, TemplateDetector, detect_player, draw_detections
from controller import KeyboardController
from state_machine import BotStateMachine, Observation

def configure_logging():
 config.LOG_DIR.mkdir(exist_ok=True); logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(message)s",handlers=[logging.FileHandler(config.LOG_DIR/'bot.log',encoding='utf-8'),logging.StreamHandler()])
def run(mode:str):
 configure_logging(); log=logging.getLogger(__name__); capture=GameCapture(); monster=load_monster_templates(); player=TemplateDetector(config.PLAYER_TEMPLATE_DIR,config.PLAYER_MATCH_THRESHOLD,config.MONSTER_MIN_DISTANCE); player.load()
 if not monster.templates: raise SystemExit("未找到怪物模板：请在 templates/monsters/ 添加 PNG/JPG/BMP 后重试。")
 if mode=="auto" and not player.templates: raise SystemExit("自动控制需要人物模板：请在 templates/player/ 添加模板。")
 controller=KeyboardController(enabled=mode=="auto" and not config.DEBUG_MODE); fsm=BotStateMachine(controller)
 try:
  while True:
   try:
    frame=capture.capture_game_frame(); roi=capture.capture_roi(frame); result=monster.detect(roi); p=detect_player(frame,player)
    if mode=="auto": fsm.step(Observation(result,p, emergency=controller.emergency_pressed()))
    visual=draw_detections(frame,result.detections); cv2.rectangle(visual,(config.ROI_LEFT,config.ROI_TOP),(config.ROI_LEFT+config.ROI_WIDTH,config.ROI_TOP+config.ROI_HEIGHT),(255,0,0),2)
    cv2.putText(visual,f"{fsm.state.value} monsters={len(result.detections)} attack={config.ATTACK_KEY in controller.down}",(15,30),cv2.FONT_HERSHEY_SIMPLEX,.7,(0,255,255),2)
    if mode in ("preview","detect"):
     cv2.imshow("Maple Bot Debug (q/ESC 退出)",visual)
     if cv2.waitKey(1)&0xFF in (ord('q'),27): break
    if config.SAVE_DEBUG_IMAGES: cv2.imwrite(str(config.DEBUG_DIR/'latest.jpg'),visual)
    time.sleep(config.IDLE_INTERVAL if mode!="auto" else config.APPROACH_INTERVAL)
   except CaptureError as exc:
    controller.release_all_keys(); log.warning("截图不可用：%s",exc); time.sleep(1)
 finally: controller.release_all_keys(); cv2.destroyAllWindows()
if __name__=='__main__':
 p=argparse.ArgumentParser(); p.add_argument('mode',choices=['preview','detect','auto'],nargs='?',default='preview'); run(p.parse_args().mode)
