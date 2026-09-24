"""本机 Flask 手动标注页：canvas 框选 player / monster / drop 并保存 YOLO 标签。"""
from __future__ import annotations
import argparse
from pathlib import Path
from flask import Flask, abort, jsonify, request, send_from_directory
import cv2

ROOT = Path(__file__).resolve().parent
CLASSES = ["player", "monster", "drop"]
HTML = '''<!doctype html><html><head><meta charset="utf-8"><title>Maple YOLO 标注</title><style>
body{font-family:Arial;background:#202124;color:#eee;margin:12px} #bar{display:flex;gap:10px;align-items:center;margin-bottom:10px}canvas{border:1px solid #777;max-width:98vw;cursor:crosshair}button,select{font-size:16px;padding:6px}#status{color:#7ee787}
</style></head><body><div id="bar"><button onclick="prev()">← 上一张</button><button onclick="next()">下一张 →</button><select id="kind"><option>player</option><option>monster</option><option>drop</option></select><button onclick="undo()">撤销框</button><button onclick="save()">保存 (S)</button><span id="status"></span></div><canvas id="c"></canvas><p>拖动鼠标画框；快捷键：1=player、2=monster、3=drop、S=保存、A/D=上一/下一张。绿色=player，红色=monster，青色=drop。</p><script>
let files=[],i=0,boxes=[],img=new Image(),start=null,c=document.querySelector('#c'),ctx=c.getContext('2d'); const colors={player:'#00ff66',monster:'#ff5555',drop:'#00e5ff'};
async function init(){files=await (await fetch('/api/images')).json();if(!files.length){status('没有图片：请先运行 extract_frames.py');return}load()}
function status(s){document.querySelector('#status').textContent=s} async function load(){let n=files[i];img.onload=async()=>{c.width=img.width;c.height=img.height;boxes=await (await fetch('/api/labels/'+n)).json();draw();status(`${i+1}/${files.length}: ${n}`)};img.src='/images/'+n+'?t='+Date.now()}
function draw(){ctx.drawImage(img,0,0);for(let b of boxes){ctx.strokeStyle=colors[b.cls];ctx.lineWidth=3;ctx.strokeRect(b.x,b.y,b.w,b.h);ctx.fillStyle=colors[b.cls];ctx.fillText(b.cls,b.x+3,Math.max(12,b.y-3))}if(start){ctx.strokeStyle='#fff';ctx.strokeRect(start.x,start.y,start.w,start.h)}}
function point(e){let r=c.getBoundingClientRect();return{x:(e.clientX-r.left)*c.width/r.width,y:(e.clientY-r.top)*c.height/r.height}}
c.onmousedown=e=>{let p=point(e);start={x:p.x,y:p.y,w:0,h:0}};c.onmousemove=e=>{if(!start)return;let p=point(e);start.w=p.x-start.x;start.h=p.y-start.y;draw()};c.onmouseup=e=>{if(!start)return;let b=start;start=null;if(Math.abs(b.w)>3&&Math.abs(b.h)>3){if(b.w<0){b.x+=b.w;b.w=-b.w}if(b.h<0){b.y+=b.h;b.h=-b.h}b.cls=document.querySelector('#kind').value;boxes.push(b)}draw()};
function undo(){boxes.pop();draw()} async function save(){let r=await fetch('/api/labels/'+files[i],{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({boxes})});status((await r.json()).message)}function next(){if(i<files.length-1){i++;load()}}function prev(){if(i>0){i--;load()}}document.onkeydown=e=>{if(e.key==='a')prev();if(e.key==='d')next();if(e.key==='s')save();if('123'.includes(e.key)){document.querySelector('#kind').selectedIndex=+e.key-1}};init();
</script></body></html>'''

def create_app(images: Path, labels: Path) -> Flask:
    app = Flask(__name__); images.mkdir(parents=True, exist_ok=True); labels.mkdir(parents=True, exist_ok=True)
    @app.get("/")
    def index(): return HTML
    @app.get("/images/<path:name>")
    def image(name: str): return send_from_directory(images, name)
    @app.get("/api/images")
    def image_list(): return jsonify([p.name for p in sorted(images.iterdir()) if p.suffix.lower() in {".jpg", ".jpeg", ".png"}])
    @app.get("/api/labels/<path:name>")
    def get_labels(name: str):
        label = labels / f"{Path(name).stem}.txt"; image = cv2.imread(str(images / name))
        if image is None: abort(404)
        h,w=image.shape[:2]; output=[]
        if label.exists():
            for line in label.read_text().splitlines():
                cls,x,y,bw,bh=map(float,line.split()); output.append({"cls":CLASSES[int(cls)],"x":(x-bw/2)*w,"y":(y-bh/2)*h,"w":bw*w,"h":bh*h})
        return jsonify(output)
    @app.post("/api/labels/<path:name>")
    def save_labels(name: str):
        image=cv2.imread(str(images / name))
        if image is None: abort(404)
        h,w=image.shape[:2]; lines=[]
        for box in request.json.get("boxes",[]):
            if box.get("cls") not in CLASSES: abort(400)
            x=max(0,min(float(box["x"]),w)); y=max(0,min(float(box["y"]),h)); bw=max(0,min(float(box["w"]),w-x)); bh=max(0,min(float(box["h"]),h-y))
            if bw >= 2 and bh >= 2: lines.append(f"{CLASSES.index(box['cls'])} {(x+bw/2)/w:.6f} {(y+bh/2)/h:.6f} {bw/w:.6f} {bh/h:.6f}")
        (labels / f"{Path(name).stem}.txt").write_text("\n".join(lines)+("\n" if lines else ""))
        return jsonify(message=f"已保存 {len(lines)} 个框")
    return app

def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("--images",type=Path,default=ROOT/"dataset/raw_frames"); parser.add_argument("--labels",type=Path,default=ROOT/"dataset/labels"); parser.add_argument("--port",type=int,default=5000); args=parser.parse_args()
    create_app(args.images,args.labels).run(host="127.0.0.1",port=args.port,debug=False)
if __name__ == "__main__": main()
