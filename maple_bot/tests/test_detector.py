import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
import numpy as np, cv2
from detector import Detection, TemplateDetector, deduplicate

def test_deduplicate_multi_template_matches():
 r=deduplicate([Detection(10,10,.95,'a'),Detection(13,13,.90,'b'),Detection(100,10,.88,'c')],10)
 assert len(r)==2 and r[0].template_name=='a'
def test_empty_template_is_unreliable(tmp_path): assert not TemplateDetector(tmp_path,.8,10).detect(np.zeros((30,30,3),np.uint8)).reliable
def test_no_monster_is_reliable(tmp_path):
 cv2.imwrite(str(tmp_path/'x.png'),np.full((5,5),255,np.uint8)); d=TemplateDetector(tmp_path,.99,10); d.load(); r=d.detect(np.zeros((30,30,3),np.uint8)); assert r.reliable and r.detections==[]
def test_roi_offset_conversion(tmp_path):
 t=np.zeros((4,4),np.uint8); t[1,2]=255; cv2.imwrite(str(tmp_path/'x.png'),t); frame=np.zeros((20,20,3),np.uint8); frame[5:9,6:10]=cv2.cvtColor(t,cv2.COLOR_GRAY2BGR); d=TemplateDetector(tmp_path,.99,1,(100,200)); d.load(); r=d.detect(frame); assert any(x.x==108 and x.y==207 for x in r.detections)
